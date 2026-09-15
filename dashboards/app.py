"""
Stakeholder-facing dashboard. Reads only from the `marts` and `staging`
schemas — never from `raw` — because marts is the business-ready layer
that's safe to show to a non-technical audience.

Run:
    streamlit run dashboards/app.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import pandas as pd
import plotly.express as px
import streamlit as st

from db import get_engine

st.set_page_config(page_title="Sales & Churn Dashboard", layout="wide")

engine = get_engine()


@st.cache_data(ttl=300)
def load_data():
    transactions = pd.read_sql("SELECT * FROM staging.transactions_clean", engine)
    churn_scores = pd.read_sql("SELECT * FROM marts.customer_churn_scores", engine)
    quality_log = pd.read_sql(
        "SELECT * FROM staging.quality_log ORDER BY run_id DESC LIMIT 12", engine
    )
    return transactions, churn_scores, quality_log


try:
    transactions, churn_scores, quality_log = load_data()
except Exception as e:
    st.error(
        "Couldn't load data from the database. Have you run the pipeline yet? "
        "Try: `python scripts/run_pipeline.py`"
    )
    st.exception(e)
    st.stop()

# --- Header: single health score ---
st.title("E-commerce Sales & Churn Health")

total_revenue = transactions[~transactions["is_return"]]["line_revenue"].sum()
at_risk_revenue = churn_scores[churn_scores["churn_risk"] == "High"]["total_revenue"].sum()
health_pct = 100 * (1 - (at_risk_revenue / total_revenue)) if total_revenue else 0

col1, col2, col3 = st.columns(3)
col1.metric("Revenue Health Score", f"{health_pct:.0f}%")
col2.metric("Total Revenue (all-time)", f"${total_revenue:,.0f}")
col3.metric("Revenue at High Churn Risk", f"${at_risk_revenue:,.0f}")

st.divider()

# --- Weekly revenue trend vs prior 4-week average ---
st.subheader("Weekly Revenue Trend")

sales = transactions[~transactions["is_return"]].copy()
sales["invoice_date"] = pd.to_datetime(sales["invoice_date"])
sales["week"] = sales["invoice_date"].dt.to_period("W").apply(lambda p: p.start_time)
weekly_revenue = sales.groupby("week")["line_revenue"].sum().reset_index()
weekly_revenue["prior_4wk_avg"] = weekly_revenue["line_revenue"].rolling(4).mean()

fig = px.line(
    weekly_revenue, x="week", y=["line_revenue", "prior_4wk_avg"],
    labels={"value": "Revenue ($)", "week": "Week", "variable": ""},
)
st.plotly_chart(fig, use_container_width=True)

st.divider()

# --- Top 10 at-risk customers by revenue ---
left, right = st.columns(2)

with left:
    st.subheader("Top 10 At-Risk Customers by Revenue")
    top_at_risk = (
        churn_scores[churn_scores["churn_risk"].isin(["High", "Medium"])]
        .sort_values("total_revenue", ascending=False)
        .head(10)[["customer_id", "churn_risk", "recency_days", "total_revenue"]]
    )
    st.dataframe(top_at_risk, use_container_width=True, hide_index=True)

with right:
    st.subheader("Country Breakdown")
    country_revenue = (
        sales.groupby("country")["line_revenue"].sum()
        .sort_values(ascending=False).head(10).reset_index()
    )
    fig2 = px.bar(country_revenue, x="country", y="line_revenue",
                  labels={"line_revenue": "Revenue ($)", "country": ""})
    st.plotly_chart(fig2, use_container_width=True)

st.divider()

# --- Data quality monitoring ---
st.subheader("Data Quality Monitoring (recent pipeline runs)")
st.dataframe(
    quality_log[["run_timestamp", "total_rows", "null_customer_id",
                 "negative_qty", "duplicate_rows", "rows_after_cleaning"]],
    use_container_width=True, hide_index=True,
)
