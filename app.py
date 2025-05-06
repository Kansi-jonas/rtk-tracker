# app.py
import pandas as pd
import requests
from flask import Flask, redirect
import os

app = Flask(__name__)

# === KONSTANTEN ===
CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"

# === CSV EINMAL LADEN ===
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df.set_index("Apollo Contact Id", inplace=True)


@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df.index:
        print(f"❌ Lead ID {lead_id} not found.")
        return redirect(REDIRECT_URL)

    lead = df.loc[lead_id].to_dict()

    payload = {
        "fields": {
            "TITLE": f"Free Trial Lead: {lead.get('Company', '')}",
            "NAME": lead.get("First Name", ""),
            "LAST_NAME": lead.get("Last Name", ""),
            "EMAIL": [{"VALUE": lead.get("Email", ""), "VALUE_TYPE": "WORK"}],
            "PHONE": [{"VALUE": lead.get("Corporate Phone", ""), "VALUE_TYPE": "WORK"}],
            "COMPANY_TITLE": lead.get("Company", ""),
            "ADDRESS_CITY": lead.get("City", ""),
            "ADDRESS_STATE": lead.get("State", ""),
            "ADDRESS_COUNTRY": lead.get("Country", ""),
            "SOURCE_ID": "EMAIL",
            "STATUS_ID": PHASE_ID,
            "UTM_CAMPAIGN": "mail-campaign",
            "UTM_SOURCE": "apollo"
        }
    }

    try:
        r = requests.post(BITRIX_WEBHOOK, json=payload)
        r.raise_for_status()
        response_json = r.json()
        print(f"✅ Lead {lead_id} created in Bitrix. Response: {response_json}")
    except Exception as e:
        print(f"❌ Error while creating lead {lead_id}: {e}")

    return redirect(REDIRECT_URL)


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")

