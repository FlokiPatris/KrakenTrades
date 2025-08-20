import pytest
import shutil

from main import main
from src.kraken_core.constants import FileLocations
from src.helpers.file_helper import get_output_dir
from tests.assertions import assert_script_generates_excel


@pytest.fixture(autouse=True)
def clean_output_dir():
    """
    Ensure output dir is clean before/after each test.
    """
    output_dir = get_output_dir()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    yield

    shutil.rmtree(output_dir)


def test_script_generates_excel():
    """
    Smoke test: run script and check Excel report is generated.
    """

    # Run the script
    main()

    # Use centralized assertion helpers
    assert_script_generates_excel(
        get_output_dir(), FileLocations.PARSED_TRADES_EXCEL.name
    )
