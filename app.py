# app.py
import pandas as pd
import requests
from flask import Flask, redirect, request
import json
import os
from datetime import datetime, timedelta

app = Flask(__name__)

# === KONSTANTEN ===
CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"
CREATED_TRACK_FILE = "created_leads.txt"
MAX_AUTO_CLICK_AGE_SECONDS = 20  # Zeitfenster, in dem automatische Klicks ignoriert werden

# === CSV laden und vorbereiten ===
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df.columns = df.columns.str.strip()
df["Apollo Contact Id"] = df["Apollo Contact Id"].str.strip()
df.set_index("Apollo Contact Id", inplace=True)

# === Hilfsfunktion ===
def safe_field(value):
    return value.strip() if isinstance(value, str) and value.strip() else None

# === Route /t/<lead_id> ===
@app.route("/t/<lead_id>")
def track_click(lead_id):
    lead_id = lead_id.strip()

    # HEAD-Request ignorieren
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

    lead = df.loc[[lead_id]].iloc[0]

    timestamp_str = lead.get("Timestamp", "").strip()
    if timestamp_str:
        try:
            timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
            age = datetime.utcnow() - timestamp
            if age.total_seconds() < MAX_AUTO_CLICK_AGE_SECONDS:
                print(f"🚫 Klick war zu schnell nach Versand: {lead_id} ({age.total_seconds()}s)")
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

    if not payload["fields"].get("NAME") or not payload["fields"].get("LAST_NAME") or not payload["fields"].get("COMPANY_TITLE"):
        print(f"❌ Unvollständige Felder für {lead_id}.")
        return redirect(REDIRECT_URL)

    print("📤 Sende Lead an Bitrix:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(BITRIX_WEBHOOK, json=payload)
        print("🔄 Bitrix-Antwort:", response.text)
        response.raise_for_status()
        print(f"✅ Lead {lead_id} erfolgreich angelegt.")

        with open(CREATED_TRACK_FILE, "a") as f:
            f.write(f"{lead_id}\n")

    except Exception as e:
        print(f"❌ Fehler beim Senden des Leads {lead_id}: {e}")

    return redirect(REDIRECT_URL)

# === Starten ===
if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")
