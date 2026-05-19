import json
import pandas as pd
import os

# Base project directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Input JSON file
input_file = os.path.join(
    BASE_DIR,
    "data",
    "raw",
    "luse_historical_prices.json"
)

# Output CSV file
output_file = os.path.join(
    BASE_DIR,
    "data",
    "processed",
    "luse_historical_prices.csv"
)

# Load JSON
with open(input_file, "r", encoding="utf-8") as f:
    data = json.load(f)

rows = []

# Flatten the JSON structure
for company in data:
    ticker = company["companyName"]
    chart_data = company["chart.data"]

    for entry in chart_data:
        rows.append({
            "ticker": ticker,
            "date": entry.get("Date"),
            "price": entry.get("Adj"),
            "volume": entry.get("Volume")
        })

# Create DataFrame
df = pd.DataFrame(rows)

# Convert date column
df["date"] = pd.to_datetime(df["date"], errors="coerce")

# Sort data
df = df.sort_values(by=["ticker", "date"])

# Save CSV
df.to_csv(output_file, index=False)

print("✅ Transformation complete!")
print(df.head())

print(f"\nCSV saved to:\n{output_file}")