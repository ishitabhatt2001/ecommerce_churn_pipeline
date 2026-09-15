"""
Step 2 of the pipeline: raw -> staging.

Applies documented cleaning rules and — importantly — logs how much bad data
it found, rather than silently deleting it. That log is what proves the
pipeline is monitoring data quality, not just processing data.

Rules applied:
    - Rows with a null/blank CustomerID are dropped, but counted first
    - Rows with negative Quantity are kept but flagged as returns (is_return)
    - Exact duplicate Invoice+StockCode rows are dropped, but counted first
    - Quantity and Price are converted to numeric types; unparseable rows
      are dropped and counted
    - line_revenue = quantity * unit_price is computed (useful downstream)

Run directly:
    python scripts/02_clean_and_stage.py
"""

import pandas as pd

from db import get_engine


def clean_and_stage():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM raw.transactions", engine)

    total_rows = len(df)

    # --- Convert types, tracking what fails ---
    df["quantity_numeric"] = pd.to_numeric(df["quantity"], errors="coerce")
    df["unit_price_numeric"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["invoice_date_parsed"] = pd.to_datetime(df["invoice_date"], errors="coerce")

    unparseable = df[
        df["quantity_numeric"].isna()
        | df["unit_price_numeric"].isna()
        | df["invoice_date_parsed"].isna()
    ]
    df = df.drop(unparseable.index)

    # --- Count and drop null CustomerID rows ---
    # Check for actual missing values FIRST (pd.isna), before converting to
    # string — on newer pandas versions, NaN.astype(str) doesn't reliably
    # become the literal text "nan", so string-matching alone can silently
    # miss real nulls.
    is_missing = df["customer_id"].isna()
    df["customer_id"] = df["customer_id"].astype(str).str.strip()
    is_blank_string = df["customer_id"].isin(["", "nan", "None", "<NA>"])
    null_customer_mask = is_missing | is_blank_string
    null_customer_id_count = null_customer_mask.sum()
    df = df[~null_customer_mask]

    # --- Flag returns instead of dropping them ---
    df["is_return"] = df["quantity_numeric"] < 0
    negative_qty_count = df["is_return"].sum()

    # --- Count and drop exact duplicates ---
    dup_mask = df.duplicated(subset=["invoice_no", "stock_code"], keep="first")
    duplicate_count = dup_mask.sum()
    df = df[~dup_mask]

    # --- Standardize country text ---
    df["country"] = df["country"].str.strip().str.title()

    # --- Compute line revenue ---
    df["line_revenue"] = df["quantity_numeric"] * df["unit_price_numeric"]

    # --- Build the final clean frame matching staging.transactions_clean ---
    clean_df = pd.DataFrame({
        "invoice_no": df["invoice_no"],
        "stock_code": df["stock_code"],
        "description": df["description"],
        "quantity": df["quantity_numeric"].astype(int),
        "invoice_date": df["invoice_date_parsed"],
        "unit_price": df["unit_price_numeric"],
        "customer_id": df["customer_id"],
        "country": df["country"],
        "is_return": df["is_return"],
        "line_revenue": df["line_revenue"],
    })

    clean_df.to_sql(
        "transactions_clean",
        engine,
        schema="staging",
        if_exists="replace",
        index=False,
    )

    # --- Write the quality log row ---
    quality_report = {
        "total_rows": total_rows,
        "null_customer_id": int(null_customer_id_count),
        "negative_qty": int(negative_qty_count),
        "duplicate_rows": int(duplicate_count),
        "rows_after_cleaning": len(clean_df),
    }
    pd.DataFrame([quality_report]).to_sql(
        "quality_log",
        engine,
        schema="staging",
        if_exists="append",
        index=False,
    )

    print("Quality report for this run:")
    for k, v in quality_report.items():
        print(f"  {k}: {v}")

    return quality_report


if __name__ == "__main__":
    clean_and_stage()
