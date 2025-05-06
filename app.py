# app.py
import pandas as pd
import requests
from flask import Flask, redirect, request
import json
import os

app = Flask(__name__)

# === KONSTANTEN ===
CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"
CREATED_TRACK_FILE = "created_leads.txt"

# === CSV laden und Index bereinigen ===
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df["Apollo Contact Id"] = df["Apollo Contact Id"].str.strip()  # <- Wichtig!
df.set_index("Apollo Contact Id", inplace=True)

# === Helferfunktion für saubere Felder ===
def safe_field(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

# === Route ===
@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    lead_id = lead_id.strip()  # <- Sicherstellen, dass es kein Leerzeichen enthält

    # HEAD-Request ignorieren (z. B. von Link-Vorschau)
    if request.method == "HEAD":
        print(f"🔁 HEAD-Request ignoriert für {lead_id}")
        return "", 204

    if lead_id not in df.index:
        print(f"❌ Lead ID {lead_id} nicht in CSV gefunden.")
        return redirect(REDIRECT_URL)

    # Duplikatprüfung
    if os.path.exists(CREATED_TRACK_FILE):
        with open(CREATED_TRACK_FILE, "r") as f:
            if lead_id in f.read().splitlines():
                print(f"⚠️ Lead {lead_id} bereits angelegt – überspringe.")
                return redirect(REDIRECT_URL)

    lead = df.loc[lead_id]

    fields = {
        "TITLE": f"Free Trial Lead: {safe_field(lead.get('Company'))}",
        "NAME": safe_field(lead.get("First Name")),
        "LAST_NAME": safe_field(lead.get("Last Name")),
        "EMAIL": [{"VALUE": safe_field(lead.get("Email")), "VALUE_TYPE": "WORK"}] if safe_field(lead.get("Email")) else [],
        "PHONE": [{"VALUE": safe_field(lead.get("Corporate Phone")), "VALUE_TYPE": "WORK"}] if safe_field(lead.get("Corporate Phone")) else [],
        "COMPANY_TITLE": safe_field(lead.get("Company")),
        "ADDRESS_CITY": safe_field(lead.get("City")),
        "ADDRESS_STATE": safe_field(lead.get("State")),
        "ADDRESS_COUNTRY": safe_field(lead.get("Country")),
        "SOURCE_ID": "EMAIL",
        "STATUS_ID": PHASE_ID,
        "UTM_CAMPAIGN": "mail-campaign",
        "UTM_SOURCE": "apollo"
    }

    # Leere Felder entfernen
    payload = {"fields": {k: v for k, v in fields.items() if v not in [None, "", []]}}

    # Debug-Log
    print("📤 Sending payload to Bitrix:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(BITRIX_WEBHOOK, json=payload)
        print("🔄 Bitrix response:", response.text)
        response.raise_for_status()
        print(f"✅ Lead {lead_id} erfolgreich angelegt.")

        # Lead-ID merken
        with open(CREATED_TRACK_FILE, "a") as f:
            f.write(f"{lead_id}\n")

    except Exception as e:
        print(f"❌ Fehler bei Lead {lead_id}: {e}")

    return redirect(REDIRECT_URL)

# === Start der App ===
if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
