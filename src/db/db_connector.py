# =============================================================================
# 🧰 Environment & Config
# =============================================================================
from __future__ import annotations

import psycopg2
from psycopg2 import OperationalError, extensions

from kraken_core import custom_logger, PostgresConfig


# =============================================================================
# 🛠️ Helper Functions
# =============================================================================
def connect_db(db_config: PostgresConfig) -> extensions.connection:
    """
    Connect to a PostgreSQL database and return the connection object.
    Caller is responsible for closing it.

    Logs detailed connection info (without exposing password) and propagates
    OperationalError if connection fails.

    Parameters
    ----------
    db_config : PostgresConfig
        Database connection configuration.

    Returns
    -------
    psycopg2.extensions.connection
        Active database connection.

    Raises
    ------
    OperationalError
        If the connection cannot be established.
    """
    custom_logger.info(
        "🔗 Connecting to DB: host=%s, port=%s, db=%s, user=%s",
        db_config.host,
        db_config.port,
        db_config.dbname,
        db_config.user,
    )

    try:
        conn: extensions.connection = psycopg2.connect(
            host=db_config.host,
            port=db_config.port,
            dbname=db_config.dbname,
            user=db_config.user,
            password=db_config.password,
            connect_timeout=5,
        )
        custom_logger.info("✅ Database connection established successfully!")
        return conn

    except OperationalError as err:
        custom_logger.error("❌ Could not connect to DB: %s", err)
        raise  # Fail-fast: propagate to caller
