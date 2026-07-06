"""
Upload CSV data to Supabase tables.
Usage: python3 upload_to_supabase.py

Inserts fresh data into empty tables.
"""
import pandas as pd
import numpy as np
from supabase import create_client
import time

SUPABASE_URL = "https://pkqekyvzwtarmjujcfva.supabase.co"
SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InBrcWVreXZ6d3Rhcm1qdWpjZnZhIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NzkyMDc4MzAsImV4cCI6MjA5NDc4MzgzMH0.cl1FFhofy4QxLq330pl6nQLRwMkCS6Y7rlWQpD1lLyo"
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

BATCH_SIZE = 500


def clean_nan(obj):
    """Recursively replace NaN/Inf with None in dicts/lists for JSON compliance."""
    if isinstance(obj, dict):
        return {k: clean_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [clean_nan(v) for v in obj]
    elif isinstance(obj, float):
        if np.isnan(obj) or np.isinf(obj):
            return None
        return obj
    return obj


def upload_csv_to_table(csv_path, table_name, batch_size=BATCH_SIZE):
    """Upload a CSV file to a Supabase table in batches."""
    print(f"\n{'='*60}")
    print(f"Uploading: {csv_path}")
    print(f"Table: {table_name}")
    print(f"{'='*60}")

    df = pd.read_csv(csv_path)
    print(f"Total rows: {len(df)}")
    print(f"Columns: {df.columns.tolist()}")

    # Convert to list of dicts and clean NaN values
    records = df.to_dict(orient="records")
    records = [clean_nan(r) for r in records]

    total = len(records)
    uploaded = 0

    for i in range(0, total, batch_size):
        batch = records[i : i + batch_size]
        try:
            resp = supabase.table(table_name).insert(batch).execute()
            uploaded += len(batch)
            print(f"  ✓ Uploaded {uploaded}/{total} rows ({uploaded/total*100:.1f}%)")
        except Exception as e:
            print(f"  ✗ Error at batch {i//batch_size + 1}: {e}")
            # Try one row at a time
            print(f"  Retrying row by row...")
            for j, row in enumerate(batch):
                try:
                    supabase.table(table_name).insert([row]).execute()
                    uploaded += 1
                except Exception as e2:
                    print(f"    ✗ Row {i+j+1} failed: {e2}")
            print(f"  ✓ Uploaded {uploaded}/{total} rows ({uploaded/total*100:.1f}%)")
            time.sleep(0.5)

    # Verify using efficient count query (limit 1 with count=exact is faster than select all)
    try:
        resp = supabase.table(table_name).select("id", count="exact").limit(1).execute()
        print(f"\nVerification: {resp.count} rows in {table_name}")
    except Exception:
        # Fallback: just report uploaded count
        print(f"\nVerification: {uploaded} rows uploaded to {table_name}")
    return uploaded


# Upload prices
upload_csv_to_table(
    "data/processed/luse_historical_prices_for_supabase.csv",
    "luse_historical_prices",
)

# Upload index
upload_csv_to_table(
    "data/processed/luse_index.csv",
    "luse_index",
)

print("\n✅ Upload complete!")
