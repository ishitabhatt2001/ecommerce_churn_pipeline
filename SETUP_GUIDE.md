# Setup Guide (for first-timers with Postgres/Python)

Follow this in order. Don't skip ahead — each step assumes the last one worked.

## Step 0 — Install the tools

**Python**: You likely have it. Check with:
```bash
python --version
```
Need 3.9+. If missing, install from python.org.

**PostgreSQL**: This is the database.
- Mac: `brew install postgresql@16` then `brew services start postgresql@16`
- Windows: download the installer from postgresql.org — it includes pgAdmin,
  a GUI you can use instead of the command line if you prefer
- Linux: `sudo apt install postgresql postgresql-contrib`

After installing, confirm it's running:
```bash
psql --version
```

**Create a database** (run once):
```bash
psql -U postgres
```
Inside the psql prompt that opens:
```sql
CREATE DATABASE ecommerce_churn;
\q
```

## Step 1 — Get the dataset

Go to Kaggle and search "Online Retail II" (UCI dataset, ~1M rows of UK
e-commerce transactions). Download it as CSV. It will have columns like:
`Invoice, StockCode, Description, Quantity, InvoiceDate, Price, Customer ID, Country`

Save the CSV into this project's `raw/` folder as `raw/online_retail_ii.csv`.

Don't have a Kaggle account or want to skip this? Run:
```bash
python scripts/00_generate_fake_data.py
```
This generates a synthetic dataset with the same messiness (nulls, negative
quantities, duplicates) so you can build and test everything without waiting
on a download.

## Step 2 — Python environment

```bash
cd ecommerce_churn_pipeline 
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

## Step 3 — Configure your database connection

```bash
cp .env.example .env
```
Open `.env` and fill in the password you set for Postgres. Everything else
can usually stay as the default (`localhost`, port `5432`, user `postgres`,
database `ecommerce_churn`).

## Step 4 — Create the schemas and raw table

You have two options here — use whichever is comfortable. If `psql` isn't
recognized in your terminal (common on Windows if Postgres wasn't added to
PATH), just use Option B — pgAdmin does everything the command line does.

**Option A — Command line:**
```bash
psql -U postgres -d ecommerce_churn -f sql/01_create_schemas.sql
psql -U postgres -d ecommerce_churn -f sql/02_create_raw_table.sql
```
If that worked, you'll see `CREATE SCHEMA` / `CREATE TABLE` printed with no
errors.

**Option B — pgAdmin (no command line needed):**
1. Open pgAdmin → expand Servers → PostgreSQL → right-click Databases →
   Create → Database, name it `ecommerce_churn`, Save.
2. Click on `ecommerce_churn` → Tools menu → Query Tool.
3. Open `sql/01_create_schemas.sql` in a text editor, copy all the text,
   paste it into the Query Tool, click Execute (▶ or F5).
4. Clear the Query Tool, repeat with `sql/02_create_raw_table.sql`.
5. Confirm it worked: expand `ecommerce_churn` → Schemas — you should see
   `raw`, `staging`, and `marts` listed, each with tables inside.

Once the schemas and tables exist, you won't need `psql` or pgAdmin's Query
Tool again — the rest of the pipeline runs entirely through Python.

## Step 5 — Run the pipeline

```bash
python scripts/run_pipeline.py
```
This runs, in order:
1. Load raw CSV into `raw.transactions`
2. Clean + validate into `staging.transactions_clean` (logs a quality report)
3. Score churn risk into `marts.customer_churn_scores`

Check your terminal output — it prints row counts and quality flags at each
step so you can see it working.

## Step 6 — View the dashboard

```bash
streamlit run dashboards/app.py
```
This opens in your browser at `http://localhost:8501`.

## Step 7 — Automate it (once everything above works)

See the comments at the bottom of `scripts/run_pipeline.py` for the cron
line to schedule a weekly run. Alerting (Slack/email) is in
`scripts/04_alert.py` — you'll need to add a webhook URL or SMTP credentials
to `.env` for that step.

## Troubleshooting

- **`psql: command not found` / `'psql' is not recognized`**: Postgres
  isn't on your PATH. Either add `<your Postgres install dir>\bin` to your
  PATH environment variable and restart your terminal, or just use
  Option B (pgAdmin) in Step 4 instead — no PATH fix needed.
- **`FATAL: password authentication failed`**: double check `.env` matches
  the password you set in Step 0.
- **`ModuleNotFoundError`**: your venv isn't activated — re-run the
  `source venv/bin/activate` line.
- **CSV column names don't match the scripts**: Kaggle's "Online Retail II"
  sometimes ships as `Invoice`/`Customer ID` instead of `InvoiceNo`/
  `CustomerID`. Open `scripts/01_load_raw.py` and adjust the `COLUMN_MAP`
  dictionary at the top — it's built exactly for this.
