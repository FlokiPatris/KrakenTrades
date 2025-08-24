# tests/scripts/test_scan_repo_root.py
import pytest

from kraken_core import RepoScanConfig, PathsConfig
from kraken_core import FolderType
from helpers import file_helper
from scripts.scan_repo import scan_repository, log_repo_structure

repo_config = RepoScanConfig()
tested_folders = [
    repo_config.CATEGORIES_TO_SCAN
]  # wrapping into [] needed for looping through frozenset


@pytest.fixture(autouse=True)
def reports_dir():
    """Fixture to prepare the report directory before each test."""
    file_helper.reset_dir(FolderType.REPORTS)

    yield PathsConfig.REPORTS_DIR


@pytest.mark.parametrize("scanned_folders", tested_folders)
def test_scan_repo_root(scanned_folders, reports_dir):
    """Test scanning the repository root generates category files without errors."""
    # Run repo structure logging
    try:
        log_repo_structure(repo_config)
    except Exception as e:
        pytest.fail(f"Logging repo structure failed: {e}")

    # Run scanning
    try:
        scan_repository(repo_config)
    except Exception as e:
        pytest.fail(f"Scanning repository failed: {e}")

    # Check that files are created for each category
    for category in scanned_folders:
        file_path = reports_dir / f"{category}.txt"
        print(f"Checking for output file: {file_path}, {category}")

        assert file_path.exists(), f"Expected output file missing: {file_path}"
        assert file_path.stat().st_size > 0, f"Output file is empty: {file_path}"
