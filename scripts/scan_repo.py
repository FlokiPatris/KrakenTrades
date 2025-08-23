"""
Repository scanning and logging utility for Kraken Trades pipeline.

Walks through repo directories, logs structure, and extracts
files into category-based text outputs according to top-level folders:
.ci, .github, scripts, src, tests, and other.
"""

import os
from pathlib import Path
from typing import Optional

from kraken_core import custom_logger, RepoScanConfig
from helpers import clean_previous_output, safe_write, safe_read, get_tree_structure


# --------------------------------------------------------------------
# Top-level Folder Categories
# --------------------------------------------------------------------
def get_category(file_path: Path, repo_root: Path, config: RepoScanConfig) -> str:
    """Determine category based on top-level folder."""
    try:
        relative_parts = file_path.relative_to(repo_root).parts
        if relative_parts:
            top_folder = relative_parts[0]
            if top_folder in config.TOP_LEVEL_CATEGORIES:
                return top_folder
    except Exception:
        pass
    return "other"


# --------------------------------------------------------------------
# Repository Tree Logging
# --------------------------------------------------------------------
def log_repo_structure(config: RepoScanConfig) -> None:
    """Logs the repository structure once to logger and output file."""
    tree_output = get_tree_structure(Path(config.REPO_ROOT), config.TREE_DEPTH)
    if not tree_output:
        return

    custom_logger.info("📁 Repository structure:\n%s", tree_output)
    safe_write(
        config.OUTPUT_FILE,
        f"\n{config.SEPARATOR}\nREPOSITORY STRUCTURE\n{config.SEPARATOR}\n{tree_output}",
        mode="w",
    )


# --------------------------------------------------------------------
# File Scanning
# --------------------------------------------------------------------
def scan_file(
    file_path: Path, config: RepoScanConfig, repo_root: Path, output_dir: Path
) -> None:
    """Reads a file safely and writes it to the corresponding category output."""
    content: Optional[str] = safe_read(
        file_path, getattr(config, "MAX_FILE_SIZE", 10 * 1024 * 1024)
    )
    if content is None:
        return

    category = get_category(file_path, repo_root, config)
    category_file = output_dir / f"{category}.txt"

    custom_logger.info("📄 %s -> %s", file_path, category_file)
    safe_write(
        category_file,
        f"\n{config.SEPARATOR}\nFILE: {file_path}\n{config.SEPARATOR}\n{content}",
        mode="a",
    )


def scan_repository(config: RepoScanConfig) -> None:
    """Walks the repo and scans files into category-based outputs."""
    repo_root = Path(config.REPO_ROOT)
    output_dir = Path(config.OUTPUT_FILE).parent

    for root, dirs, files in os.walk(repo_root):
        dirs[:] = [
            d for d in dirs if not d.startswith(".") or d in config.TOP_LEVEL_CATEGORIES
        ]
        for file in files:
            file_path = Path(root) / file
            if file_path.suffix.lower() in config.INCLUDED_EXTENSIONS:
                scan_file(file_path, config, repo_root, output_dir)


# --------------------------------------------------------------------
# Main Orchestration
# --------------------------------------------------------------------
def main() -> None:
    config = RepoScanConfig()
    repo_root = Path(config.REPO_ROOT)
    output_file = Path(config.OUTPUT_FILE)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    if not repo_root.exists():
        custom_logger.error("❌ Repository root does not exist: %s", repo_root)
        return

    # Clean old outputs
    clean_previous_output(output_file)
    for category in config.TOP_LEVEL_CATEGORIES + ["other"]:
        clean_previous_output(output_file.parent / f"{category}.txt")

    custom_logger.info("🔍 Scanning repository at: %s", repo_root)

    log_repo_structure(config)
    scan_repository(config)

    custom_logger.info(
        "✅ Extraction complete! Category files saved in %s", output_file.parent
    )


if __name__ == "__main__":
    main()
