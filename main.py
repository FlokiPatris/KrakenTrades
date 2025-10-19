#!/usr/bin/env python3
"""
Main pipeline for processing Kraken trade PDFs into styled Excel reports.

- Reads input PDF from configured uploads directory.
- Extracts trade records.
- Builds Pandas DataFrames.
- Writes and styles an Excel report.
- Fully Docker and CI/CD friendly.
"""

import sys

from file_management import (build_trade_dataframe,
                             extract_kraken_trade_records_from_pdf,
                             style_excel, write_portfolio_report)
from helpers import file_helper
from kraken_core import custom_logger


def main() -> None:
    """Run the full Kraken trade PDF → Excel."""
    try:
        if not file_helper.KRAKEN_TRADES_PDF.exists():
            custom_logger.error(
                "❌ Input PDF does not exist: %s", file_helper.KRAKEN_TRADES_PDF
            )
            sys.exit(1)

        custom_logger.info(
            "📄 Extracting trade records from PDF: %s", file_helper.KRAKEN_TRADES_PDF
        )
        extracted_records = extract_kraken_trade_records_from_pdf(
            file_helper.KRAKEN_TRADES_PDF
        )

        custom_logger.info("📊 Building DataFrames from extracted records")
        formatted_dfs = build_trade_dataframe(extracted_records)

        custom_logger.info(
            "💾 Writing Excel report to: %s", file_helper.PARSED_TRADES_EXCEL
        )
        write_portfolio_report(formatted_dfs, file_helper.PARSED_TRADES_EXCEL)
        style_excel(file_helper.PARSED_TRADES_EXCEL)

        custom_logger.info(
            "✅ Report successfully written: %s", file_helper.PARSED_TRADES_EXCEL
        )

    except Exception as exc:
        custom_logger.exception("🔥 Pipeline failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
