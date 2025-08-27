# =============================================================================
# 📦 Imports
# =============================================================================
from psycopg2.extensions import connection as PsycopgConnection
from pydantic import BaseModel

from kraken_core import custom_logger

# =============================================================================
# 📌 Constants
# =============================================================================
EXPECTED_SERVER_VERSION: int = 170004  # Example: PostgreSQL 17.4
CONNECTION_OPEN: int = 0


# =============================================================================
# 🐍 Pydantic Model
# =============================================================================
class ConnectionInfoModel(BaseModel):
    server_version: int
    closed: int
    dsn: str
    encoding: str


# =============================================================================
# 🔧 DB params
# =============================================================================
def extract_connection_info(conn: PsycopgConnection) -> ConnectionInfoModel:
    data = {attr: getattr(conn, attr) for attr in ConnectionInfoModel.model_fields}
    return ConnectionInfoModel(**data)


def assert_db_params(conn: PsycopgConnection) -> None:
    conn_info = extract_connection_info(conn)

    assert conn_info.server_version == EXPECTED_SERVER_VERSION, (
        f"Server version must be exactly {EXPECTED_SERVER_VERSION}, "
        f"got {conn_info.server_version}"
    )
    assert (
        conn_info.closed == CONNECTION_OPEN
    ), f"Connection must be open, got closed={conn_info.closed}"
    custom_logger.info("Database connection parameters verified successfully.")
