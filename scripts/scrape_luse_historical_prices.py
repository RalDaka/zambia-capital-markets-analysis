import json
import re
import os
from seleniumbase import SB

TICKER_MAP = {
    "ZNCO": "zanaco", "ZCCM": "zccm", "ZMBF": "zamb", "ZFCO": "zfco",
    "ZSUG": "zmsg", "ZMFA": "zamefa", "ZABR": "zambrw", "SHOP": "shoprt",
    "ZMRE": "prima", "MAFS": "mfin", "BATZ": "batz", "BATA": "bata",
    "AECI": "aeci", "CECA": "ceca", "CECZ": "cec", "REIZ": "reiz",
    "DCZM": "dczm", "ATEL": "atel", "NATB": "natbrw", "SCBL": "scz",
    "CHIL": "chil", "PUMA": "puma"
}

def load_existing_data(file_path):
    """Loads existing JSON data into a dictionary for fast lookup."""
    if os.path.exists(file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = json.load(f)
                # Convert list to dict: { "AECI": [data], "ZNCO": [data] }
                return {item['companyName']: item['chart.data'] for item in content}
        except Exception as e:
            print(f"⚠️ Could not read existing JSON: {e}. Starting fresh.")
    return {}

def main():
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    output_file = os.path.join(
        BASE_DIR,
        "data",
        "raw",
        "luse_historical_prices.json"
)
    
    # 1. Load what we already have on the Mac
    existing_records = load_existing_data(output_file)
    print(f"📂 Loaded existing data for {len(existing_records)} companies.")

    all_updated_data = []

    with SB(uc=True, headless=True) as sb:
        for ticker, slug in TICKER_MAP.items():
            url = f"https://africanfinancials.com/company/zm-{slug}/"
            print(f"🔍 Checking {ticker}...")
            
            try:
                sb.uc_open_with_reconnect(url, reconnect_time=4)
                source = sb.get_page_source()
                pattern = r'chart\.data\s*=\s*(\[.*?\]);'
                match = re.search(pattern, source, re.DOTALL)

                if match:
                    web_data = json.loads(match.group(1))
                    
                    # 2. Get existing dates for this specific ticker
                    local_data = existing_records.get(ticker, [])
                    local_dates = {entry['Date'] for entry in local_data}
                    
                    # 3. Only keep web entries that ARE NOT in our local dates
                    new_entries = [entry for entry in web_data if entry['Date'] not in local_dates]
                    
                    if new_entries:
                        print(f"   ✨ Found {len(new_entries)} NEW records for {ticker}!")
                        # Merge: Old Data + New Data
                        merged_data = local_data + new_entries
                        # Re-sort by date to keep the JSON tidy
                        merged_data.sort(key=lambda x: x['Date'])
                    else:
                        print(f"   ✅ {ticker} is already up to date.")
                        merged_data = local_data

                    all_updated_data.append({
                        "companyName": ticker,
                        "chart.data": merged_data
                    })
                else:
                    print(f"   ⚠️ Pattern not found for {ticker}.")
                    # Keep the old data if the scrape fails
                    if ticker in existing_records:
                        all_updated_data.append({"companyName": ticker, "chart.data": existing_records[ticker]})

            except Exception as e:
                print(f"   ❌ Error: {str(e)[:50]}")

            sb.sleep(1)

    # 4. Save the expanded master list back to the JSON
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(all_updated_data, f, indent=2, ensure_ascii=False)
    
    print(f"\n✅ Sync Complete! Updated JSON saved at: {output_file}")

if __name__ == "__main__":
    main()