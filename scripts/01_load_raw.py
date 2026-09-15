"""
Step 1 of the pipeline: load the raw CSV into Postgres, exactly as-is.

We deliberately do NOT clean or convert types here. The raw schema's job is
to be an untouched copy of what arrived — that way, if a bug is later found
in the cleaning logic, you can always re-run it against the same raw data
without re-downloading anything.

Run directly:
    python scripts/01_load_raw.py
"""

import sys

import pandas as pd

from db import get_engine

CSV_PATH = "raw/online_retail_ii.csv"

# Kaggle's "Online Retail II" sometimes ships with slightly different column
# names depending on the export. Adjust this map if your CSV's headers
# don't match the keys on the left.
COLUMN_MAP = {
    "Invoice": "invoice_no",
    "InvoiceNo": "invoice_no",
    "StockCode": "stock_code",
    "Description": "description",
    "Quantity": "quantity",
    "InvoiceDate": "invoice_date",
    "Price": "unit_price",
    "UnitPrice": "unit_price",
    "Customer ID": "customer_id",
    "CustomerID": "customer_id",
    "Country": "country",
}


def load_raw():
    try:
        df = pd.read_csv(CSV_PATH, dtype=str)  # read everything as text on purpose
    except FileNotFoundError:
        print(f"Could not find {CSV_PATH}.")
        print("Either download the Kaggle dataset into raw/, or run:")
        print("    python scripts/00_generate_fake_data.py")
        sys.exit(1)

    # Rename whichever of the known column-name variants are present.
    df = df.rename(columns={k: v for k, v in COLUMN_MAP.items() if k in df.columns})

    expected_cols = ["invoice_no", "stock_code", "description", "quantity",
                      "invoice_date", "unit_price", "customer_id", "country"]
    missing = [c for c in expected_cols if c not in df.columns]
    if missing:
        print(f"WARNING: expected columns not found after renaming: {missing}")
        print(f"Columns present: {list(df.columns)}")
        print("Update COLUMN_MAP at the top of this script to match your CSV.")
        sys.exit(1)

    df = df[expected_cols]

    engine = get_engine()
    df.to_sql(
        "transactions",
        engine,
        schema="raw",
        if_exists="replace",  # each run replaces raw with the latest source file
        index=False,
    )
    print(f"Loaded {len(df)} rows into raw.transactions")
    return len(df)


if __name__ == "__main__":
    load_raw()
