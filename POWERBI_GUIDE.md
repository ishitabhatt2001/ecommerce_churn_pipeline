# Power BI Dashboard Guide

Power BI and the Streamlit dashboard both read from the same `marts` and
`staging` tables in Postgres — you don't need to change or duplicate any
pipeline logic. Run `python scripts/run_pipeline.py` first so those tables
have data, then follow this guide.

## Step 1 — Connect Power BI to Postgres

1. Open Power BI Desktop → **Home** → **Get Data** → **More...**
2. Search for **PostgreSQL database** → **Connect**
   - If this is your first time, Power BI will prompt you to install the
     Npgsql .NET driver — click the link it gives you, install it, then
     restart Power BI Desktop.
3. Enter:
   - **Server**: `localhost:5432` (or your host/port from `.env`)
   - **Database**: `ecommerce_churn`
4. Choose **DirectQuery** if you want the dashboard to always show live data
   without manual refreshes, or **Import** if you'd rather load a snapshot
   (faster to work with, needs a manual "Refresh" click to update).
   For a portfolio project, **Import** is simpler and fine.
5. Enter your Postgres username/password when prompted.
6. In the Navigator window, check these tables and click **Load**:
   - `marts.customer_churn_scores`
   - `staging.transactions_clean`
   - `staging.quality_log`

## Step 2 — Build a date table (needed for the weekly trend)

Power BI needs an explicit date table to do week-over-week comparisons
cleanly. In the **Modeling** tab → **New Table**, paste:

```
DateTable = CALENDAR(MIN(transactions_clean[invoice_date]), MAX(transactions_clean[invoice_date]))
```

Then in **Modeling** → **Mark as Date Table**, select `DateTable` and its
`Date` column. Go to **Model view** and drag a relationship from
`DateTable[Date]` to `transactions_clean[invoice_date]`.

## Step 3 — DAX measures

Create these under **Modeling** → **New Measure** (matches what the
Streamlit dashboard shows):

```
Total Revenue =
CALCULATE(
    SUM(transactions_clean[line_revenue]),
    transactions_clean[is_return] = FALSE
)
```

```
At-Risk Revenue =
CALCULATE(
    SUM(customer_churn_scores[total_revenue]),
    customer_churn_scores[churn_risk] = "High"
)
```

```
Health Score % =
DIVIDE(
    [Total Revenue] - [At-Risk Revenue],
    [Total Revenue],
    0
) * 100
```

```
Weekly Revenue =
CALCULATE(
    [Total Revenue],
    DATESBETWEEN(
        DateTable[Date],
        STARTOFWEEK(SELECTEDVALUE(DateTable[Date])),
        ENDOFWEEK(SELECTEDVALUE(DateTable[Date]))
    )
)
pending
```

```
Prior 4-Week Avg Revenue =
AVERAGEX(
    DATESINPERIOD(DateTable[Date], LASTDATE(DateTable[Date]), -28, DAY),
    [Weekly Revenue]
)
```

```
High Risk Customer Count =
CALCULATE(
    DISTINCTCOUNT(customer_churn_scores[customer_id]),
    customer_churn_scores[churn_risk] = "High"
)
```

## Step 4 — Build the visuals

Recreate the same layout as the Streamlit dashboard:

| Visual | Type | Fields |
|---|---|---|
| Health Score | Card | `Health Score %` |
| Total Revenue | Card | `Total Revenue` |
| Revenue at Risk | Card | `At-Risk Revenue` |
| Weekly Revenue Trend | Line chart | Axis: `DateTable[Date]` (by week), Values: `Weekly Revenue`, `Prior 4-Week Avg Revenue` |
| Top 10 At-Risk Customers | Table, sorted descending | `customer_id`, `churn_risk`, `recency_days`, `total_revenue`; filter `churn_risk` in {High, Medium}, Top N filter = 10 by `total_revenue` |
| Country Breakdown | Bar chart | Axis: `transactions_clean[country]`, Values: `Total Revenue` |
| Data Quality Monitoring | Table | all columns from `quality_log`, sorted by `run_timestamp` descending |

## Step 5 — Refresh

- **Import mode**: click **Refresh** in the Home ribbon after each pipeline
  run, or set up a Power BI Gateway + scheduled refresh if you publish this
  to the Power BI service.
- **DirectQuery mode**: no refresh needed, it queries Postgres live — but
  visuals will feel slower, especially on the full Kaggle dataset (~1M rows).

## Step 6 — Save and export

Save as `dashboards/churn_dashboard.pbix`. For your GitHub repo, a `.pbix`
file is binary and doesn't diff well in git — the standard move is to also
export a PDF or PNG screenshot of the finished dashboard (**File** →
**Export** → **Export to PDF**) and commit that alongside the `.pbix`, so
recruiters can see it without opening Power BI.

## Why have both dashboards?

For a portfolio project, showing both signals range: Streamlit shows you can
build a data app in code (useful if the target role touches any
Python/web work), while Power BI shows the more traditional BI-tool skillset
many analyst job postings explicitly ask for. Mentioning "built dashboards in
both Streamlit and Power BI, reading from the same warehouse" is a strong,
literal resume line.
