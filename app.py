import pandas as pd
import requests
from flask import Flask, redirect, request
import json
import os
from datetime import datetime, timezone
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

SERVICE_ACCOUNT_FILE = os.getenv(
    "SERVICE_ACCOUNT_FILE",
    "/etc/secrets/rtk-tracker-sync-094bc2e32f0b.json"
)

SHEET_NAME = "RTK Lead Tracking"
WORKSHEET_NAME = "Sheet1"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"
CREATED_TRACK_FILE = "created_leads.txt"
MAX_AUTO_CLICK_AGE_SECONDS = 20

def get_sheet():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    creds = ServiceAccountCredentials.from_json_keyfile_name(SERVICE_ACCOUNT_FILE, scope)
    client = gspread.authorize(creds)
    return client.open(SHEET_NAME).worksheet(WORKSHEET_NAME)

def fetch_data():
    sheet = get_sheet()
    df = pd.DataFrame(sheet.get_all_records()).fillna("")
    df.columns = df.columns.str.strip()
    df["Apollo Contact Id"] = df["Apollo Contact Id"].str.strip()
    df.set_index("Apollo Contact Id", inplace=True)
    return df

def safe_field(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

def set_cell(email, column_name, value):
    try:
        sheet = get_sheet()
        records = sheet.get_all_records()
        header_row = sheet.row_values(1)

        col_number = header_row.index(column_name) + 1 if column_name in header_row else None
        if col_number is None:
            print(f"🔴 Spalte '{column_name}' nicht gefunden.")
            return False

        row_number = None
        for idx, record in enumerate(records, start=2):
            record_email = record.get("Email", "").strip().lower()
            if record_email == email.strip().lower():
                row_number = idx
                break

        if row_number:
            sheet.update_cell(row_number, col_number, value)
            print(f"🟢 {column_name} auf '{value}' gesetzt für {email}")
            return True
        else:
            print(f"🔴 E-Mail {email} nicht gefunden.")
    except Exception as e:
        print(f"⚠️ Fehler beim Setzen von {column_name}: {e}")

    return False

@app.route("/t/<lead_id>")
def track_click(lead_id):
    df = fetch_data()

    if request.method == "HEAD":
        print(f"🔁 HEAD ignoriert: {lead_id}")
        return "", 204

    if lead_id not in df.index:
        print(f"❌ Lead-ID {lead_id} nicht gefunden.")
        return redirect(REDIRECT_URL)

    if os.path.exists(CREATED_TRACK_FILE):
        with open(CREATED_TRACK_FILE, "r") as f:
            if lead_id in f.read().splitlines():
                print(f"⚠️ Lead {lead_id} bereits erstellt.")
                return redirect(REDIRECT_URL)

    lead = df.loc[lead_id]

    timestamp_str = lead.get("Send Timestamp", "").strip()
    if timestamp_str:
        try:
            timestamp = datetime.fromisoformat(timestamp_str)
            age = datetime.now(timezone.utc) - timestamp
            if age.total_seconds() < MAX_AUTO_CLICK_AGE_SECONDS:
                print(f"🚫 Klick zu schnell nach Versand: {lead_id} ({age.total_seconds()}s)")
                return redirect(REDIRECT_URL)
        except Exception as e:
            print(f"⚠️ Ungültiger Timestamp bei {lead_id}: {e}")

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

    payload = {"fields": {k: v for k, v in fields.items() if v not in [None, "", []]}}

    lead_email = safe_field(lead.get("Email"))
    if not lead_email:
        print("🔴 Keine E-Mail gefunden, Click Timestamp nicht möglich.")
        return redirect(REDIRECT_URL)

    try:
        response = requests.post(BITRIX_WEBHOOK, json=payload)
        response.raise_for_status()
        print(f"✅ Lead {lead_id} erfolgreich angelegt.")

        with open(CREATED_TRACK_FILE, "a") as f:
            f.write(f"{lead_id}\n")

        # NEU: Click Timestamp setzen
        set_cell(lead_email, "Click Timestamp", datetime.now(timezone.utc).isoformat())

        # NEU: Clicked auf TRUE setzen
        set_cell(lead_email, "Clicked", "TRUE")

    except Exception as e:
        print(f"❌ Fehler beim Senden des Leads {lead_id}: {e}")

    return redirect(REDIRECT_URL)

if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
