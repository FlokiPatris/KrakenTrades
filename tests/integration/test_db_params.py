# =============================================================================
# 📦 Imports
# =============================================================================
import pytest

from kraken_core import PostgresConfig, custom_logger
from db import connect_db
from tests.assertions.database import assert_db_params


# =============================================================================
# 🔧 Fixtures
# =============================================================================
@pytest.fixture(scope="module")
def db_config() -> PostgresConfig:
    """
    Load real DB config from environment variables.
    Fail-fast if missing.
    """
    return PostgresConfig.from_env()


# =============================================================================
# 🧪 E2E Test
# =============================================================================
@pytest.mark.skip(
    reason="Requires proper routing and public, unchanging IP of the test env"
)
def test_db_params(db_config: PostgresConfig) -> None:
    """
    Connect to a real database and verify critical parameters.
    Uses helper from tests/assertions/database.py.
    """
    try:
        with connect_db(db_config) as conn:
            # ✅ Use existing helper to assert connection parameters
            assert_db_params(conn)

    except Exception as e:
        custom_logger.exception("❌ Test failed due to unexpected error: %s", e)
        raise
