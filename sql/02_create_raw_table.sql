-- Run once, after 01_create_schemas.sql.
-- The raw table intentionally uses loose types (TEXT) because raw data is
-- messy — we don't want the load step to fail just because a quantity field
-- has a stray character in it. Type conversion and validation happen in the
-- staging step instead, where we can log problems rather than crash on them.

CREATE TABLE IF NOT EXISTS raw.transactions (
    invoice_no      TEXT,
    stock_code      TEXT,
    description     TEXT,
    quantity        TEXT,
    invoice_date    TEXT,
    unit_price      TEXT,
    customer_id     TEXT,
    country         TEXT,
    loaded_at       TIMESTAMP DEFAULT now()
);

-- The quality log is the proof-of-monitoring table mentioned in the README.
-- One row gets inserted every time the pipeline runs.
CREATE TABLE IF NOT EXISTS staging.quality_log (
    run_id              SERIAL PRIMARY KEY,
    run_timestamp       TIMESTAMP DEFAULT now(),
    total_rows          INTEGER,
    null_customer_id    INTEGER,
    negative_qty        INTEGER,
    duplicate_rows      INTEGER,
    rows_after_cleaning INTEGER
);

-- Cleaned, typed, deduplicated data lands here.
CREATE TABLE IF NOT EXISTS staging.transactions_clean (
    invoice_no      TEXT,
    stock_code      TEXT,
    description     TEXT,
    quantity        INTEGER,
    invoice_date    TIMESTAMP,
    unit_price      NUMERIC(10, 2),
    customer_id     TEXT,
    country         TEXT,
    is_return       BOOLEAN,
    line_revenue    NUMERIC(12, 2)
);

-- Final business-ready churn scores, one row per customer.
CREATE TABLE IF NOT EXISTS marts.customer_churn_scores (
    customer_id         TEXT PRIMARY KEY,
    last_purchase_date  TIMESTAMP,
    recency_days        INTEGER,
    frequency_90d        INTEGER,
    avg_order_value     NUMERIC(10, 2),
    total_revenue        NUMERIC(12, 2),
    rfm_score            INTEGER,
    churn_risk           TEXT,
    scored_at            TIMESTAMP DEFAULT now()
);
