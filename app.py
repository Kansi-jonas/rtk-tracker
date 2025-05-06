from flask import Flask, redirect, request
import pandas as pd
import requests

app = Flask(__name__)

CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/rxpcf8a0u3undrgc/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"  # Mail Kampagne

df = pd.read_csv(CSV_PATH, dtype=str).fillna("")

@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df['Apollo Contact Id'].values:
        return redirect(REDIRECT_URL)

    lead = df[df['Apollo Contact Id'] == lead_id].iloc[0]

    lead_data = {
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
        response = requests.post(BITRIX_WEBHOOK, json=lead_data)
        response.raise_for_status()
        return redirect(REDIRECT_URL)
    except Exception as e:
        print(f"Error adding lead to Bitrix: {e}")
        return redirect(REDIRECT_URL)

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
