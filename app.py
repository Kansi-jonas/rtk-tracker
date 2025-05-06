from flask import Flask, redirect, request
import pandas as pd
import requests
import logging
import os

app = Flask(__name__)

# === KONFIGURATION ===
CSV_PATH = "apollo-contacts-export.csv"  # relativer Pfad für Render
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/rxpcf8a0u3undrgc/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"  # Mail Kampagne

# === LOGGER EINRICHTEN ===
logging.basicConfig(filename='click_tracker.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# === CSV LADEN ===
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV-Datei nicht gefunden unter Pfad: {CSV_PATH}")

df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df.set_index("Apollo Contact Id", inplace=True)

@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df.index:
        logging.warning(f"Invalid lead_id: {lead_id}")
        return redirect(REDIRECT_URL)

    lead = df.loc[lead_id]

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
        logging.info(f"Lead added to Bitrix: {lead_id} - {lead.get('Email', '')}")
    except Exception as e:
        logging.error(f"Bitrix Error for {lead_id}: {e}")

    return redirect(REDIRECT_URL)

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
