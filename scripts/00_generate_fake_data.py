"""
Optional: generates a synthetic e-commerce dataset with the same shape and
messiness as the real "Online Retail II" dataset, so you can build and test
the whole pipeline without waiting on a Kaggle download.

Run:
    python scripts/00_generate_fake_data.py

Output:
    raw/online_retail_ii.csv
"""

import random
import string
from datetime import datetime, timedelta

import pandas as pd

random.seed(42)

WORDS = ["LANTERN", "MUG", "CANDLE", "BASKET", "FRAME", "CUSHION", "TRAY",
         "CLOCK", "VASE", "BOWL", "NOTEBOOK", "BLANKET", "MIRROR", "HOOK"]


def fake_stock_code():
    letters = "".join(random.choices(string.ascii_uppercase, k=2))
    digits = "".join(random.choices(string.digits, k=4))
    return letters + digits


def fake_description():
    return f"{random.choice(WORDS)} {random.choice(WORDS)}"

N_CUSTOMERS = 500
N_ROWS = 20000
COUNTRIES = ["United Kingdom", "Germany", "France", "EIRE", "Spain", "Netherlands"]

# Give each customer a "purchase behavior" so RFM scoring later has real
# signal to find — some customers buy often and recently (loyal), some
# haven't bought in months (churn risk).
customer_ids = [str(10000 + i) for i in range(N_CUSTOMERS)]
customer_profile = {
    cid: random.choice(["loyal", "at_risk", "new", "churned"])
    for cid in customer_ids
}


def random_date_for_profile(profile):
    today = datetime.now()
    if profile == "loyal":
        days_ago = random.randint(0, 20)
    elif profile == "new":
        days_ago = random.randint(0, 10)
    elif profile == "at_risk":
        days_ago = random.randint(60, 100)
    else:  # churned
        days_ago = random.randint(150, 400)
    return today - timedelta(days=days_ago)


rows = []
for _ in range(N_ROWS):
    cid = random.choice(customer_ids)
    profile = customer_profile[cid]
    invoice_date = random_date_for_profile(profile)
    quantity = random.randint(1, 20)

    # Inject the same messiness the real dataset has:
    if random.random() < 0.05:
        cid = ""  # missing CustomerID
    if random.random() < 0.03:
        quantity = -quantity  # return

    rows.append(
        {
            "Invoice": str(random.randint(500000, 599999)),
            "StockCode": fake_stock_code(),
            "Description": fake_description(),
            "Quantity": quantity,
            "InvoiceDate": invoice_date.strftime("%Y-%m-%d %H:%M:%S"),
            "Price": round(random.uniform(0.5, 50.0), 2),
            "Customer ID": cid,
            "Country": random.choice(COUNTRIES),
        }
    )

df = pd.DataFrame(rows)

# Inject some exact duplicate rows on purpose (Invoice + StockCode)
duplicate_sample = df.sample(frac=0.02, random_state=1)
df = pd.concat([df, duplicate_sample], ignore_index=True)

df.to_csv("raw/online_retail_ii.csv", index=False)
print(f"Wrote {len(df)} rows to raw/online_retail_ii.csv")
print(f"  - {(df['Customer ID'] == '').sum()} rows with missing Customer ID")
print(f"  - {(df['Quantity'] < 0).sum()} rows with negative quantity (returns)")
print(f"  - {df.duplicated(subset=['Invoice', 'StockCode']).sum()} duplicate Invoice+StockCode rows")
