"""
File helper utilities for Kraken Trades pipeline.

Provides safe file I/O, directory resolution, and cleanup utilities
suitable for CI/CD, Docker, and secure financial pipelines.
"""

from pathlib import Path
import subprocess
from typing import Optional

from kraken_core import FileLocations, custom_logger

# --------------------------------------------------------------------
# Directory Resolution
# --------------------------------------------------------------------


def get_tree_structure(root_path: Path, depth: int) -> str:
    """Return a safe textual tree structure for a directory."""
    try:
        return subprocess.check_output(
            ["tree", "-L", str(depth), str(root_path)], text=True
        )
    except Exception as e:
        custom_logger.warning("⚠️ Could not generate tree: %s", e)
        return ""


def ensure_dir(path: Path) -> Path:
    """Ensure a directory exists, create if missing."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def get_output_dir() -> Path:
    """Return the folder for writing output files."""
    return ensure_dir(FileLocations.UPLOADS_DIR)


def get_report_path() -> Path:
    """Return full path for the Excel report."""
    return get_output_dir() / FileLocations.PARSED_TRADES_EXCEL.name


def get_input_pdf_path() -> Path:
    """Return full path to input Kraken trades PDF."""
    return get_output_dir() / FileLocations.KRAKEN_TRADES_PDF.name


# --------------------------------------------------------------------
# File Operations
# --------------------------------------------------------------------


def safe_write(file_path: Path, content: str, mode: str = "a") -> None:
    """
    Safely write content to a file.

    Args:
        file_path: Target file path.
        content: Text content to write.
        mode: File open mode (default: append).
    """
    try:
        with file_path.open(mode, encoding="utf-8") as f:
            f.write(content)
    except Exception as e:
        custom_logger.error("❌ Failed writing to %s: %s", file_path, e)


def safe_read(file_path: Path, max_size: int = 10 * 1024 * 1024) -> Optional[str]:
    """
    Safely read a file if smaller than max_size.

    Args:
        file_path: Path to read.
        max_size: Maximum file size in bytes (default 10MB).

    Returns:
        File content as string or None if skipped.
    """
    try:
        size = file_path.stat().st_size
        if size > max_size:
            custom_logger.warning(
                "⏩ Skipping large file: %s (%d bytes)", file_path, size
            )
            return None
        return file_path.read_text(encoding="utf-8")
    except Exception as e:
        custom_logger.error("❌ Could not read %s: %s", file_path, e)
        return None


# --------------------------------------------------------------------
# Directory Cleanup
# --------------------------------------------------------------------


def clean_previous_output(file_path: Path) -> None:
    """
    Delete previous output file if it exists.

    Args:
        file_path: Path to output file.
    """
    if file_path.exists():
        try:
            file_path.unlink()
            custom_logger.info("🧹 Previous output file deleted: %s", file_path)
        except Exception as e:
            custom_logger.warning("⚠️ Could not delete previous output file: %s", e)
