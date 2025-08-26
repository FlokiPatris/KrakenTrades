# --------------------------------------------------------------------
# 🧰 Environment & Config
# --------------------------------------------------------------------
from __future__ import annotations
import psycopg2
from psycopg2 import OperationalError

from kraken_core import custom_logger
from kraken_core import PostgresConfig


# --------------------------------------------------------------------
# 🛠️ Helper Functions
# --------------------------------------------------------------------
def connect_db(db_config: PostgresConfig) -> psycopg2.extensions.connection:
    """
    Connect to PostgreSQL and return the connection object.
    Caller is responsible for closing it.
    Raises OperationalError if connection fails.
    """
    try:
        custom_logger.info(
            f"🔗 Connecting to DB as user: {db_config.user}, port: {db_config.port}"
        )
        conn = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            dbname=db_config.dbname,
            user=db_config.user,
            password=db_config.password,
            connect_timeout=5,
        )
        custom_logger.info("✅ Connection established successfully!")
        return conn

    except OperationalError as e:
        custom_logger.error("❌ Could not connect to DB: %s", e)
        raise  # propagate to caller
