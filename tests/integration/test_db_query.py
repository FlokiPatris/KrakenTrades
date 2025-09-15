# =============================================================================
# 📦 Imports
# =============================================================================
import pytest
from kraken_core import PostgresConfig, custom_logger
from db import connect_db


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
# 🧪 E2E Test with multiple queries
# =============================================================================
@pytest.mark.parametrize(
    "query, expected",
    [
        ("SELECT 1", 1),
        ("SELECT 2", 2),
        ("SELECT 3 + 4", 7),
    ],
)
@pytest.mark.skip(
    reason="Requires proper routing and public, unchanging IP of the test env"
)
def test_db_queries(db_config: PostgresConfig, query: str, expected: int) -> None:
    """
    Connect to a real database and assert multiple simple queries.
    """
    try:
        with connect_db(db_config) as conn:
            with conn.cursor() as cur:
                cur.execute(query)
                result = cur.fetchone()

                assert result is not None, f"Query `{query}` returned no result"
                assert (
                    result[0] == expected
                ), f"Query `{query}` expected {expected}, got {result[0]}"

    except Exception as e:
        custom_logger.exception("❌ Test failed for query `%s`: %s", query, e)
        raise
