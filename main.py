#!/usr/bin/env python3
"""
Main pipeline for processing Kraken trade PDFs into styled Excel reports.

- Reads input PDF from configured uploads directory.
- Extracts trade records.
- Builds Pandas DataFrames.
- Writes and styles an Excel report.
- Fully Docker and CI/CD friendly.
"""

from pathlib import Path
import sys

from helpers.file_helper import get_output_dir
from file_management import (
    build_trade_dataframe,
    extract_kraken_trade_records_from_pdf,
    style_excel,
    write_excel,
)
from kraken_core import FileLocations
from kraken_core import custom_logger


def main() -> None:
    """Run the full Kraken trade PDF → Excel."""
    try:
        # Resolve input PDF path
        input_pdf: Path = FileLocations.KRAKEN_TRADES_PDF
        if not input_pdf.exists():
            custom_logger.error("❌ Input PDF does not exist: %s", input_pdf)
            sys.exit(1)

        custom_logger.info("📄 Extracting trade records from PDF: %s", input_pdf)
        extracted_records = extract_kraken_trade_records_from_pdf(input_pdf)

        custom_logger.info("📊 Building DataFrames from extracted records")
        formatted_dfs = build_trade_dataframe(extracted_records)

        # Determine output folder and final Excel path
        output_dir: Path = get_output_dir()
        output_file: Path = output_dir / FileLocations.PARSED_TRADES_EXCEL.name

        custom_logger.info("💾 Writing Excel report to: %s", output_file)
        write_excel(formatted_dfs, output_file)
        style_excel(output_file)

        custom_logger.info("✅ Report successfully written: %s", output_file)

    except Exception as exc:
        custom_logger.exception("🔥 Pipeline failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
