# =============================================================================
# 🧩 Test Module: test_scan_repo_root.py
# =============================================================================
from pathlib import Path
from typing import Generator, List

import pytest

from kraken_core import RepoScanConfig, PathsConfig, FolderType
from helpers import file_helper
from scripts.scan_repo import scan_repository, log_repo_structure

# =============================================================================
# 🔧 Test Config
# =============================================================================
repo_config = RepoScanConfig()
# Wrap frozenset in a list for pytest.parametrized iteration
tested_folders: List[frozenset] = [repo_config.CATEGORIES_TO_SCAN]


# =============================================================================
# 🧹 Fixtures
# =============================================================================
@pytest.fixture(autouse=True)
def reports_dir() -> Generator[Path, None, None]:
    """
    Prepare and clean the reports directory before each test.

    Yields:
        Path: The path to the reports directory.
    """
    # Pre-test cleanup
    file_helper.reset_dir(FolderType.REPORTS)
    yield PathsConfig.REPORTS_DIR
    # Post-test cleanup (safe-guard)
    file_helper.reset_dir(FolderType.REPORTS)


# =============================================================================
# ⚡ Test Cases
# =============================================================================
@pytest.mark.parametrize("scanned_folders", tested_folders)
@pytest.mark.e2e
def test_scan_repo_root(scanned_folders: frozenset, reports_dir: Path) -> None:
    """
    Test that scanning the repository root generates category files without errors.
    """

    # Run repository structure logging
    log_repo_structure(repo_config)

    # Run scanning
    scan_repository(repo_config)

    # Helper: assert file existence and non-empty
    def assert_file_valid(file_path: Path) -> None:
        assert file_path.exists(), f"Expected output file missing: {file_path}"
        assert file_path.stat().st_size > 0, f"Output file is empty: {file_path}"

    # Check that files are created for each category
    for category in scanned_folders:
        file_path = reports_dir / f"{category}.txt"
        print(f"Checking for output file: {file_path}, {category}")
        assert_file_valid(file_path)
