from flask import Flask, redirect, request
import pandas as pd
import requests
import logging
import os

# === Konfiguration ===
app = Flask(__name__)

# Pfad zur CSV-Datei und Bitrix Webhook URL
CSV_PATH = "apollo-contacts-export.csv"  # Ändere dies entsprechend deinem Speicherort
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/rxpcf8a0u3undrgc/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"  # Die Seite für den Free Trial Link
PHASE_ID = "UC_MID1CI"  # Beispiel für eine Phase "Mail Kampagne", ändere dies, falls nötig

# Logging
logging.basicConfig(filename='click_tracker.log', level=logging.INFO, format='%(asctime)s - %(message)s')

# Prüfen, ob die CSV-Datei vorhanden ist
if not os.path.exists(CSV_PATH):
    raise FileNotFoundError(f"CSV-Datei nicht gefunden unter Pfad: {CSV_PATH}")

# CSV-Datei laden
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")  # Lese die CSV-Datei ein und ersetze NaN-Werte durch leere Strings
df.set_index("Apollo Contact Id", inplace=True)  # Setze die "Apollo Contact Id" als Index für den Zugriff

@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df.index:
        logging.warning(f"Invalid lead_id: {lead_id}")
        return redirect(REDIRECT_URL)  # Wenn Lead-ID ungültig ist, leite weiter zur Trial-Seite

    lead = df.loc[lead_id].to_dict()  # Konvertiere die Series in ein Dictionary

    # Erstelle das Payload für Bitrix24
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

    # Versuche, den Lead in Bitrix zu erstellen
    try:
        response = requests.post(BITRIX_WEBHOOK, json=payload)
        response.raise_for_status()  # Raise an exception for HTTP errors
        logging.info(f"Lead successfully created in Bitrix: {lead_id} - {lead.get('Email', '')}")
    except requests.exceptions.RequestException as e:
        logging.error(f"Bitrix Error for {lead_id}: {e}")

    # Redirect zur Free Trial Seite
    return redirect(REDIRECT_URL)


if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")

