"""
Runs the full pipeline end to end, in order:
    1. Load raw CSV into raw.transactions
    2. Clean + validate into staging.transactions_clean (logs quality report)
    3. Score churn risk into marts.customer_churn_scores
    4. Send/print the run summary alert

This is the single entry point you schedule (via cron or Airflow) to make
the pipeline "self-updating" instead of something you run by hand.

Run directly:
    python scripts/run_pipeline.py
"""

import logging
import sys
import time
from pathlib import Path

# Make sure this script can be run from the project root (python scripts/run_pipeline.py)
sys.path.insert(0, str(Path(__file__).parent))

from importlib import import_module

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(message)s",
    handlers=[
        logging.FileHandler("logs/pipeline.log"),
        logging.StreamHandler(sys.stdout),
    ],
)
log = logging.getLogger(__name__)


def run_step(step_name, module_name, func_name):
    log.info(f"--- Starting: {step_name} ---")
    start = time.time()
    try:
        module = import_module(module_name)
        func = getattr(module, func_name)
        result = func()
        elapsed = time.time() - start
        log.info(f"--- Finished: {step_name} ({elapsed:.1f}s) ---")
        return result
    except Exception:
        log.exception(f"--- FAILED: {step_name} ---")
        raise


def main():
    load_raw = import_module("01_load_raw")
    clean_and_stage = import_module("02_clean_and_stage")
    churn_scoring = import_module("03_churn_scoring")
    alert = import_module("04_alert")

    run_step("Load raw data", "01_load_raw", "load_raw")
    run_step("Clean and stage", "02_clean_and_stage", "clean_and_stage")
    run_step("Score churn risk", "03_churn_scoring", "score_churn")
    run_step("Send alert", "04_alert", "send_alert")

    log.info("Pipeline run complete.")


if __name__ == "__main__":
    main()

# --- Scheduling this weekly ---
#
# Cron (simple): run `crontab -e` and add a line like this to run every
# Monday at 6am (adjust the paths to match your machine):
#
#   0 6 * * 1  cd /full/path/to/ecommerce_churn_pipeline && \
#              /full/path/to/venv/bin/python scripts/run_pipeline.py \
#              >> logs/cron.log 2>&1
#
# Airflow (stronger, more resume-worthy): wrap the four run_step() calls
# above into a DAG with one PythonOperator per step, each with
# retries=2 and retry_delay set. This demonstrates automation with
# failure-recovery, which is a real keyword recruiters scan for.
