import pandas as pd
import requests
from flask import Flask, redirect

app = Flask(__name__)

# CSV Pfad und Bitrix Webhook URL
CSV_PATH = "apollo-contacts-export.csv"  # Ersetze mit deinem tatsächlichen Pfad
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"  # Mail Kampagne

# CSV Laden
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df.set_index("Apollo Contact Id", inplace=True)


@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df.index:
        print(f"Lead ID {lead_id} not found in CSV.")
        return redirect(REDIRECT_URL)

    # Lead-Daten aus DataFrame holen
    lead = df.loc[lead_id]

    # Sicherstellen, dass wir einen sauberen Payload für die Bitrix API haben
    payload = {
        "fields": {
            "TITLE": f"Free Trial Lead: {lead['Company']}",
            "NAME": lead['First Name'],
            "LAST_NAME": lead['Last Name'],
            "EMAIL": [{"VALUE": lead['Email'], "VALUE_TYPE": "WORK"}],
            "PHONE": [{"VALUE": lead['Corporate Phone'], "VALUE_TYPE": "WORK"}],
            "COMPANY_TITLE": lead['Company'],
            "ADDRESS_CITY": lead['City'],
            "ADDRESS_STATE": lead['State'],
            "ADDRESS_COUNTRY": lead['Country'],
            "SOURCE_ID": "EMAIL",
            "STATUS_ID": PHASE_ID,
            "UTM_CAMPAIGN": "mail-campaign",
            "UTM_SOURCE": "apollo"
        }
    }

    try:
        # Bitrix API Anfrage
        r = requests.post(BITRIX_WEBHOOK, json=payload)
        r.raise_for_status()  # Wird eine Ausnahme auslösen, wenn etwas schief geht
        print(f"Lead {lead_id} was successfully created in Bitrix!")
    except requests.exceptions.RequestException as e:
        print(f"Error in creating lead for {lead_id}: {e}")

    return redirect(REDIRECT_URL)


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")

