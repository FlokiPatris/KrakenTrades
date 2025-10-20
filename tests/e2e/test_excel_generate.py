import pytest

from helpers import file_helper
from kraken_core import FolderType, PathsConfig
from main import main
from tests.assertions import assert_script_generates_excel


@pytest.fixture(autouse=True)
def clean_uploads_dir():
    """
    Ensure output dir is clean before/after each test.
    """

    file_helper.reset_dir(FolderType.UPLOADS)

    yield

@pytest.mark.skip(reason="I need to create first a way to not fetch 30d charts test is too slow")
def test_script_generates_excel():
    """
    Smoke test: run script and check Excel report is generated.
    """

    # Run the script
    main()

    # Use centralized assertion helpers
    assert_script_generates_excel(PathsConfig.PARSED_TRADES_EXCEL.name)
