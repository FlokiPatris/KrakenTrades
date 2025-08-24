"""
Repository scanning and logging utility for Kraken Trades pipeline.

This module performs a structured scan of a repository:
- Walks through directories under REPO_ROOT.
- Logs repository structure to a file and logger.
- Extracts file contents into category-based text outputs based on top-level folders defined in RepoScanConfig.
- Handles large/unreadable files safely.
- Supports reproducible, CI/CD-friendly reporting.
"""

from __future__ import annotations
import os
from pathlib import Path
from typing import Optional

from kraken_core import custom_logger, RepoScanConfig, PathsConfig, FolderType
from helpers import file_helper


# --------------------------------------------------------------------
# 🔹 Category Detection
# --------------------------------------------------------------------
def get_category(file_path: Path, repo_root: Path, config: RepoScanConfig) -> str:
    """
    Determine the category of a file based on its top-level folder.

    Args:
        file_path: Absolute path to the file.
        repo_root: Root directory of the repository.
        config: Configuration object with scan categories.

    Returns:
        Top-level folder name if recognized, else fallback category.
    """
    try:
        # Get the relative path of the file with respect to the repository root.
        # Example:
        #   repo_root = "/trades"
        #   file_path = "/trades/src/module/file.py"
        #   -> relative_parts = ("src", "module", "file.py")
        #
        # Using .parts breaks the relative path into its directory components,
        # so we can easily access the top-level folder ("src" in this case).
        relative_parts = file_path.relative_to(repo_root).parts
        if relative_parts:
            top_folder = relative_parts[0]
            if top_folder in config.CATEGORIES_TO_SCAN:
                return top_folder
    except ValueError as e:
        # file_path not under repo_root
        custom_logger.warning(
            "⚠️ File %s not under repo root %s: %s", file_path, repo_root, e
        )
    except Exception as e:
        custom_logger.error(
            "❌ Unexpected error determining category for %s: %s", file_path, e
        )
        raise

    return config.FALLBACK_CATEGORY


# --------------------------------------------------------------------
# 🔹 Repository Structure Logging
# --------------------------------------------------------------------
def log_repo_structure(config: RepoScanConfig) -> None:
    """
    Logs the repository tree structure to both logger and output file.

    Uses TREE_DEPTH from config to limit directory depth. Writes a
    human-readable structure to 'repo_tree_structure.txt'.
    """
    try:
        tree_output = file_helper.get_tree_structure(
            PathsConfig.REPO_ROOT, config.TREE_DEPTH
        )
        if not tree_output:
            custom_logger.warning(
                "⚠️ Repository tree could not be generated for %s", PathsConfig.REPO_ROOT
            )
            return

        # Log and write repository structure
        custom_logger.info("📁 Repository structure:\n%s", tree_output)
        file_helper.safe_write(
            PathsConfig.REPORTS_DIR / "repo_tree_structure.txt",
            f"\n{config.SEPARATOR}\nREPOSITORY STRUCTURE\n{config.SEPARATOR}\n{tree_output}",
            mode="w",
        )
    except Exception as e:
        custom_logger.error("❌ Failed to log repository structure: %s", e)
        raise


# --------------------------------------------------------------------
# 🔹 File Scanning & Categorization
# --------------------------------------------------------------------
def scan_file(
    file_path: Path, config: RepoScanConfig, repo_root: Path, reports_dir: Path
) -> None:
    """
    Reads a file safely and appends it to the category output file.

    - Ignores files exceeding MAX_FILE_SIZE or unreadable files.
    - Uses safe_write to append file content.
    """
    content: Optional[str] = file_helper.safe_read(
        file_path, getattr(config, "MAX_FILE_SIZE", 10 * 1024 * 1024)
    )
    if content is None:
        custom_logger.info("⚠️ Skipping file (empty or too large): %s", file_path)
        return

    category = get_category(file_path, repo_root, config)
    category_file = reports_dir / f"{category}.txt"

    custom_logger.info("📄 %s -> %s", file_path, category_file)
    try:
        file_helper.safe_write(
            category_file,
            f"\n{config.SEPARATOR}\nFILE: {file_path}\n{config.SEPARATOR}\n{content}",
            mode="a",
        )
    except Exception as e:
        custom_logger.error("❌ Failed to write file %s: %s", category_file, e)
        raise


# --------------------------------------------------------------------
# 🔹 Repository Walk & Scan
# --------------------------------------------------------------------
def scan_repository(config: RepoScanConfig) -> None:
    """
    Walks the repository directories and scans all relevant files.

    - Filters directories to scan-relevant folders.
    - Only includes files with extensions in INCLUDED_EXTENSIONS.
    """
    repo_root = PathsConfig.REPO_ROOT

    for root, dirs, files in os.walk(repo_root):
        # Keep only scan-relevant directories
        dirs[:] = [
            d for d in dirs if not d.startswith(".") or d in config.CATEGORIES_TO_SCAN
        ]

        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in config.INCLUDED_EXTENSIONS:
                scan_file(file_path, config, repo_root, file_helper.reports_dir)


# --------------------------------------------------------------------
# 🏁 Main Execution
# --------------------------------------------------------------------
def main() -> None:
    """Entry point for repository scanning utility."""
    config = RepoScanConfig()
    repo_root = PathsConfig.REPO_ROOT

    # Reset reports folder before scanning
    file_helper.reset_dir(FolderType.REPORTS)

    custom_logger.info("🔍 Scanning repository at: %s", repo_root)

    # Log tree structure once
    log_repo_structure(config)

    # Scan and extract files into category-based outputs
    scan_repository(config)

    custom_logger.info(
        "✅ Extraction complete! Category files saved in %s", PathsConfig.REPORTS_DIR
    )


# --------------------------------------------------------------------
# 🔧 Entry Point
# --------------------------------------------------------------------
if __name__ == "__main__":
    main()
