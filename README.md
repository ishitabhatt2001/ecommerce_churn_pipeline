# E-commerce Sales & Churn Analytics Pipeline

## Business Problem

Business stakeholders currently pull sales numbers manually every Monday and
have no early-warning system for customers who are about to churn.

This project builds a weekly, self-updating pipeline that:
1. Loads raw e-commerce transaction data into a real database
2. Cleans and validates it (and logs *how* messy it was, every run)
3. Scores every customer's churn risk using RFM (Recency, Frequency, Monetary)
4. Publishes a stakeholder-facing dashboard
5. Sends an automated summary alert after every run

## Architecture

```
Kaggle CSV  --->  raw schema (Postgres)   [untouched, exactly as downloaded]
                        |
                        v
             scripts/02_clean_and_stage.py
                        |
                        v
                staging schema           [cleaned, validated, deduplicated]
                        |
                        v
             scripts/03_churn_scoring.py
                        |
                        v
                 marts schema            [RFM scores, churn buckets, ready for BI]
                        |
                        v
              dashboards/app.py (Streamlit)   <-- what the stakeholder sees
                        |
                        v
              scripts/04_alert.py  --->  Slack/email summary
```

Every run also writes a row to `staging.quality_log` — a running record of
how much bad data showed up, which is what lets you prove the pipeline is
actually monitoring itself.

## Folder Structure

```
ecommerce_churn_pipeline/
├── raw/                # place the downloaded CSV here
├── sql/                # schema + table definitions, run once
├── scripts/            # the actual pipeline, run in order
├── staging/            # (empty — staging lives in Postgres, not on disk)
├── marts/              # (empty — marts lives in Postgres, not on disk)
├── dashboards/         # Streamlit app
├── logs/               # pipeline run logs land here
├── .env.example        # copy to .env and fill in your DB credentials
├── requirements.txt
├── SETUP_GUIDE.md       # start here if Postgres/Python are new to you
└── POWERBI_GUIDE.md     # connect Power BI to the same warehouse tables
```

## How to Run (short version — see SETUP_GUIDE.md for the full walkthrough)

```bash
# 1. Set up Python environment
python -m venv venv
source venv/bin/activate      # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 2. Set up Postgres and create schemas/tables
psql -U postgres -f sql/01_create_schemas.sql
psql -U postgres -f sql/02_create_raw_table.sql

# 3. Copy .env.example to .env and fill in your DB password

# 4. Download the dataset (see SETUP_GUIDE.md step 1) into raw/

# 5. Run the full pipeline
python scripts/run_pipeline.py

# 6. View the dashboard (Streamlit)
streamlit run dashboards/app.py

# 6b. Or view it in Power BI instead — see POWERBI_GUIDE.md
```

## Two Dashboards, One Warehouse

This project ships both a **Streamlit** dashboard (`dashboards/app.py`) and
a **Power BI** dashboard (see `POWERBI_GUIDE.md`). Both read from the same
`marts`/`staging` Postgres tables — no pipeline changes needed to support
either one. Build whichever you need first, or both.

## Resume Bullets (fill in real numbers once you've run it)

- Built an end-to-end ETL pipeline processing [X] transactions across raw →
  staging → marts schemas in PostgreSQL.
- Implemented automated data quality validation flagging [X]% of records for
  null CustomerID, duplicate invoices, or negative quantities before they
  reached the dashboard.
- Designed an RFM-based churn scoring model identifying [X]% of the customer
  base as high-risk, representing $[X] in at-risk revenue.
- Automated a previously manual weekly reporting process end-to-end, with
  Slack/email alerting on every run.

Only put numbers here you can explain if asked "how did you calculate that?"
