"""
Shared database connection helper.
Every other script imports get_engine() from here instead of building its
own connection — this way the connection logic (and credentials) live in
exactly one place.
"""

import os
from dotenv import load_dotenv
from sqlalchemy import create_engine

# Load variables from the .env file into the environment.
load_dotenv()


def get_engine():
    """
    Returns a SQLAlchemy engine connected to Postgres, using credentials
    from .env. An "engine" is SQLAlchemy's term for a reusable connection
    pool to the database — pandas' to_sql/read_sql functions accept it
    directly.
    """
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "ecommerce_churn")
    user = os.getenv("DB_USER", "postgres")
    password = os.getenv("DB_PASSWORD", "")

    connection_string = f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{name}"
    return create_engine(connection_string)
