"""
Shared database connection helper.
Every other script imports get_engine() from here instead of building its
own connection — this way the connection logic (and credentials) live in
exactly one place.

Credentials come from, in order:
  1. .env / environment variables   (local development and the pipeline)
  2. Streamlit secrets              (deployed app on Streamlit Cloud)
  3. Local defaults                 (localhost / ecommerce_churn)
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine
from sqlalchemy.engine import URL

# Load variables from the .env file into the environment.
load_dotenv()


def _from_streamlit_secrets():
    """Read [connections.postgresql] from Streamlit secrets, or None if absent."""
    try:
        import streamlit as st

        s = st.secrets["connections"]["postgresql"]
        return {
            "host": s["host"],
            "port": int(s.get("port", 5432)),
            "database": s["database"],
            "username": s["username"],
            "password": s["password"],
        }
    except Exception:
        return None


def get_engine():
    """
    Returns a SQLAlchemy engine connected to Postgres. An "engine" is
    SQLAlchemy's term for a reusable connection pool to the database —
    pandas' to_sql/read_sql functions accept it directly.
    """
    cfg = None

    # On Streamlit Cloud there is no .env, so neither of these is set.
    using_env = os.getenv("DB_HOST") or os.getenv("DB_PASSWORD")
    if not using_env:
        cfg = _from_streamlit_secrets()

    if cfg is None:
        cfg = {
            "host": os.getenv("DB_HOST", "localhost"),
            "port": int(os.getenv("DB_PORT", "5432")),
            "database": os.getenv("DB_NAME", "ecommerce_churn"),
            "username": os.getenv("DB_USER", "postgres"),
            "password": os.getenv("DB_PASSWORD", ""),
        }

    # URL.create handles special characters in the password safely.
    url = URL.create("postgresql+psycopg2", **cfg)
    return create_engine(url, pool_pre_ping=True)