import pandas as pd

df = pd.read_csv("C:\Users\Jobec\OneDrive\Desktop\rtk-tracker\apollo-contacts-export.csv", dtype=str).fillna("")
print("📄 Spaltennamen aus der CSV:")
print(list(df.columns))
