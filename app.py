import pandas as pd
import requests
from flask import Flask, redirect, request
import os

app = Flask(__name__)

CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"
CREATED_TRACK_FILE = "created_leads.txt"

def safe(val):
    return val.strip() if isinstance(val, str) and val.strip() else None

@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    lead_id = lead_id.strip()

    if request.method == "HEAD":
        print(f"🔁 HEAD ignoriert: {lead_id}")
        return "", 204

    try:
        df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
        df["Apollo Contact Id"] = df["Apollo Contact Id"].str.strip()
        df.set_index("Apollo Contact Id", inplace=True)
    except Exception as e:
        print(f"❌ Fehler beim Laden der CSV: {e}")
        return redirect(REDIRECT_URL)

    if lead_id not in df.index:
        print(f"❌ Lead-ID {lead_id} nicht in CSV gefunden.")
        return redirect(REDIRECT_URL)

    if os.path.exists(CREATED_TRACK_FILE):
        with open(CREATED_TRACK_FILE, "r") as f:
            if lead_id in f.read().splitlines():
                print(f"⚠️ Lead {lead_id} bereits angelegt.")
                return redirect(REDIRECT_URL)

    lead = df.loc[lead_id]

    first = safe(lead.get("First Name"))
    last = safe(lead.get("Last Name"))
    company = safe(lead.get("Company"))

    if not any([first, last, company]):
        print(f"❌ Unvollständige Felder für {lead_id}.")
        return redirect(REDIRECT_URL)

    payload = {
        "fields": {
            "TITLE": f"Free Trial Lead: {company or 'Unbekannt'}",
            "NAME": first,
            "LAST_NAME": last,
            "COMPANY_TITLE": company,
            "SOURCE_ID": "EMAIL",
            "STATUS_ID": PHASE_ID,
        }
    }

    try:
        res = requests.post(BITRIX_WEBHOOK, json=payload)
        print("📤 Bitrix response:", res.text)
        res.raise_for_status()

        with open(CREATED_TRACK_FILE, "a") as f:
            f.write(f"{lead_id}\n")

        print(f"✅ Lead {lead_id} erstellt.")
    except Exception as e:
        print(f"❌ Fehler beim Senden an Bitrix: {e}")

    return redirect(REDIRECT_URL)

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
