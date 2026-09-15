"""
Step 3 of the pipeline: staging -> marts.

Computes RFM (Recency, Frequency, Monetary) metrics per customer and buckets
each customer into a Low/Medium/High churn risk category.

This is intentionally simple, rule-based logic rather than a trained model —
production DA roles value explainable rules you can defend in an interview
over black-box scores. See the bottom of this file for the optional
logistic-regression stretch goal.

Run directly:
    python scripts/03_churn_scoring.py
"""

import pandas as pd

from db import get_engine


def score_churn():
    engine = get_engine()
    df = pd.read_sql("SELECT * FROM staging.transactions_clean", engine)

    # Returns represent negative revenue events, not purchase activity —
    # exclude them from RFM so a customer who returns everything doesn't
    # look "frequent."
    purchases = df[~df["is_return"]]

    today = pd.Timestamp.now()
    cutoff_90d = today - pd.Timedelta(days=90)

    # --- Recency: days since each customer's most recent purchase ---
    last_purchase = purchases.groupby("customer_id")["invoice_date"].max().rename("last_purchase_date")
    recency_days = (today - last_purchase).dt.days.rename("recency_days")

    # --- Frequency: distinct orders in the last 90 days ---
    recent = purchases[purchases["invoice_date"] >= cutoff_90d]
    frequency_90d = recent.groupby("customer_id")["invoice_no"].nunique().rename("frequency_90d")

    # --- Monetary: average order value and total revenue (all-time) ---
    order_totals = purchases.groupby(["customer_id", "invoice_no"])["line_revenue"].sum()
    avg_order_value = order_totals.groupby("customer_id").mean().rename("avg_order_value")
    total_revenue = purchases.groupby("customer_id")["line_revenue"].sum().rename("total_revenue")

    rfm = pd.concat(
        [last_purchase, recency_days, frequency_90d, avg_order_value, total_revenue],
        axis=1,
    ).reset_index()

    # Customers with zero purchases in the last 90 days won't appear in the
    # frequency_90d groupby at all — fill those in as 0, not missing.
    rfm["frequency_90d"] = rfm["frequency_90d"].fillna(0).astype(int)

    # --- Score each dimension 1 (worst) to 3 (best), then combine ---
    rfm["recency_score"] = pd.cut(
        rfm["recency_days"], bins=[-1, 30, 90, float("inf")], labels=[3, 2, 1]
    ).astype(int)
    rfm["frequency_score"] = pd.cut(
        rfm["frequency_90d"], bins=[-1, 0, 2, float("inf")], labels=[1, 2, 3]
    ).astype(int)
    rfm["monetary_score"] = pd.cut(
        rfm["avg_order_value"],
        bins=[-1, rfm["avg_order_value"].quantile(0.33),
              rfm["avg_order_value"].quantile(0.66), float("inf")],
        labels=[1, 2, 3],
    ).astype(int)

    rfm["rfm_score"] = rfm["recency_score"] + rfm["frequency_score"] + rfm["monetary_score"]

    # --- Bucket into churn risk ---
    def bucket(score):
        if score >= 7:
            return "Low"
        elif score >= 4:
            return "Medium"
        else:
            return "High"

    rfm["churn_risk"] = rfm["rfm_score"].apply(bucket)

    final = rfm[[
        "customer_id", "last_purchase_date", "recency_days", "frequency_90d",
        "avg_order_value", "total_revenue", "rfm_score", "churn_risk",
    ]]

    final.to_sql(
        "customer_churn_scores",
        engine,
        schema="marts",
        if_exists="replace",
        index=False,
    )

    summary = final["churn_risk"].value_counts().to_dict()
    at_risk_revenue = final[final["churn_risk"] == "High"]["total_revenue"].sum()
    print(f"Scored {len(final)} customers.")
    print(f"  Churn risk breakdown: {summary}")
    print(f"  Revenue at risk (High-risk customers): ${at_risk_revenue:,.2f}")

    return final


if __name__ == "__main__":
    score_churn()

# --- Optional stretch goal ---
# Once the rule-based version above works, you can validate it with a simple
# logistic regression: label each customer 1 if they made a purchase in the
# most recent 90-day window and 0 if not, then fit a model on
# [recency_days, frequency_90d, avg_order_value] from the *previous* period
# to see how well it predicts. If your rule-based buckets roughly agree with
# the model's risk ranking, that's a good "I validated my heuristic"
# resume/interview point. This is genuinely a stretch goal — get the
# rule-based version working and understood first.
