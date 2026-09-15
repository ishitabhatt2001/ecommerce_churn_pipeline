"""
Step 4 of the pipeline: send a summary alert after every run.

This is the "production" signal for the project: a system that tells a
human something happened, without them having to go check. Uses a Slack
incoming webhook if SLACK_WEBHOOK_URL is set in .env; otherwise just prints
the summary (so the pipeline still works with zero alerting configured).

Run directly (uses whatever is currently in the DB, doesn't re-run the
pipeline):
    python scripts/04_alert.py
"""

import os

import pandas as pd
import requests
from dotenv import load_dotenv

from db import get_engine

load_dotenv()


def build_summary():
    engine = get_engine()

    quality = pd.read_sql(
        "SELECT * FROM staging.quality_log ORDER BY run_id DESC LIMIT 1", engine
    )
    scores = pd.read_sql("SELECT churn_risk, total_revenue FROM marts.customer_churn_scores", engine)

    if quality.empty or scores.empty:
        return "Pipeline alert: no data found yet — has the pipeline run at least once?"

    q = quality.iloc[0]
    high_risk = scores[scores["churn_risk"] == "High"]

    summary = (
        f"*Weekly Pipeline Run Summary*\n"
        f"Rows processed: {q['total_rows']}\n"
        f"Rows after cleaning: {q['rows_after_cleaning']}\n"
        f"Data quality flags: {q['null_customer_id']} missing customer IDs, "
        f"{q['negative_qty']} returns, {q['duplicate_rows']} duplicates\n"
        f"New high-risk customers: {len(high_risk)}\n"
        f"Revenue at risk: ${high_risk['total_revenue'].sum():,.2f}"
    )
    return summary


def send_slack(message):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        return False
    response = requests.post(webhook_url, json={"text": message})
    return response.status_code == 200


def send_alert():
    summary = build_summary()
    sent = send_slack(summary)
    if sent:
        print("Alert sent to Slack.")
    else:
        print("SLACK_WEBHOOK_URL not set (or send failed) — printing summary instead:\n")
        print(summary)


if __name__ == "__main__":
    send_alert()
