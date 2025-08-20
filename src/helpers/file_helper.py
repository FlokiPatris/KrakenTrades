"""
File helper utilities for Kraken Trades pipeline.

This module centralizes file path resolution and ensures
consistent handling of input/output locations across
Docker containers and CI/CD pipelines.
"""

from pathlib import Path

from src.kraken_core.constants import FileLocations

# --------------------------------------------------------------------
# Directory Resolution
# --------------------------------------------------------------------


def get_output_dir() -> Path:
    """
    Return the folder for writing output files.
    Creates the folder if it does not exist.
    """
    uploads_dir: Path = FileLocations.UPLOADS_DIR

    if not uploads_dir.exists():
        uploads_dir.mkdir(parents=True, exist_ok=True)

    return uploads_dir


def get_report_path() -> Path:
    """
    Return the full path for the Excel report.
    """
    return get_output_dir() / FileLocations.PARSED_TRADES_EXCEL.name


def get_input_pdf_path() -> Path:
    """
    Return the full path to the input Kraken trades PDF.
    """
    return get_output_dir() / FileLocations.KRAKEN_TRADES_PDF.name
