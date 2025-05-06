# app.py
import pandas as pd
import requests
from flask import Flask, redirect
import json

app = Flask(__name__)

# === KONSTANTEN ===
CSV_PATH = "apollo-contacts-export.csv"
BITRIX_WEBHOOK = "https://kansi.bitrix24.de/rest/9/hno2rrrti0b3z7w6/crm.lead.add.json"
REDIRECT_URL = "https://rtkdata.com/product/free-trial-for-30-days/"
PHASE_ID = "UC_MID1CI"

# === CSV EINMAL LADEN ===
df = pd.read_csv(CSV_PATH, dtype=str).fillna("")
df.set_index("Apollo Contact Id", inplace=True)

# === Helferfunktion für saubere Felder ===
def safe_field(value):
    return value if value and str(value).strip() else None

# === Flask Route ===
@app.route("/free-trial/<lead_id>")
def track_click(lead_id):
    if lead_id not in df.index:
        print(f"❌ Lead ID {lead_id} not found in CSV.")
        return redirect(REDIRECT_URL)

    lead = df.loc[lead_id].to_dict()

    fields = {
        "TITLE": f"Free Trial Lead: {safe_field(lead.get('Company'))}",
        "NAME": safe_field(lead.get("First Name")),
        "LAST_NAME": safe_field(lead.get("Last Name")),
        "EMAIL": [{"VALUE": safe_field(lead.get("Email")), "VALUE_TYPE": "WORK"}] if lead.get("Email") else [],
        "PHONE": [{"VALUE": safe_field(lead.get("Corporate Phone")), "VALUE_TYPE": "WORK"}] if lead.get("Corporate Phone") else [],
        "COMPANY_TITLE": safe_field(lead.get("Company")),
        "ADDRESS_CITY": safe_field(lead.get("City")),
        "ADDRESS_STATE": safe_field(lead.get("State")),
        "ADDRESS_COUNTRY": safe_field(lead.get("Country")),
        "SOURCE_ID": "EMAIL",
        "STATUS_ID": PHASE_ID,
        "UTM_CAMPAIGN": "mail-campaign",
        "UTM_SOURCE": "apollo"
    }

    # Entferne leere Felder
    clean_fields = {k: v for k, v in fields.items() if v not in [None, "", []]}
    payload = {"fields": clean_fields}

    # 👉 Debug-Ausgabe
    print("📤 Sending payload to Bitrix:")
    print(json.dumps(payload, indent=2))

    try:
        response = requests.post(BITRIX_WEBHOOK, json=payload)
        print("🔄 Bitrix raw response:", response.text)
        response.raise_for_status()
        response_json = response.json()
        print(f"✅ Lead {lead_id} created. Bitrix ID: {response_json.get('result')}")
    except Exception as e:
        print(f"❌ Error while creating lead {lead_id}: {e}")

    return redirect(REDIRECT_URL)

# === App starten ===
if __name__ == "__main__":
    app.run(debug=False, port=5000, host="0.0.0.0")


