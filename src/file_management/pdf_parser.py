from pathlib import Path
from typing import List

import pandas as pd
import pdfplumber

from src.kraken_core import (
    FormatRules,
    RawColumn,
    TradeColumn,
    TradeRegex,
    custom_logger,
)


# === PDF Trade Extractor ===
def extract_kraken_trade_records_from_pdf(path: Path) -> List[dict]:
    """
    Extracts Kraken trade records from a PDF file using regex patterns.
    """
    custom_logger.info(f"📄 Starting PDF extraction from: {path}")
    records: List[dict] = []

    try:
        with pdfplumber.open(path) as pdf:
            custom_logger.debug(f"Opened PDF with {len(pdf.pages)} pages")

            for page_num, page in enumerate(pdf.pages, start=1):
                lines = page.extract_text().split("\n")
                custom_logger.debug(f"Page {page_num}: Extracted {len(lines)} lines")

                i = 0
                while i < len(lines) - 1:
                    date_line = lines[i].strip()
                    trade_line = lines[i + 1].strip()

                    if TradeRegex.DATE.match(date_line) and not trade_line.startswith(
                        "Page"
                    ):
                        merged = f"{date_line} {trade_line}"
                        match = TradeRegex.TRADE.match(merged)

                        if match:
                            records.append(match.groupdict())
                            custom_logger.debug(f"Matched trade: {match.groupdict()}")
                        else:
                            custom_logger.warning(f"Unmatched trade line: {merged}")

                        i += 2
                    else:
                        i += 1

    except Exception as e:
        custom_logger.exception(f"❌ Failed to extract trades from PDF: {e}")
        raise

    if not records:
        custom_logger.error("No trades matched — check PDF format or regex.")
        raise RuntimeError("No trades matched — check PDF format or regex.")

    custom_logger.info(f"✅ Extracted {len(records)} trade records")
    return records


# === Trade DataFrame Builder ===
def build_trade_dataframe(records: List[dict]) -> pd.DataFrame:
    """
    Converts raw trade records into a formatted DataFrame with standardized columns.
    """
    custom_logger.info(f"🔧 Building trade DataFrame from {len(records)} records")
    df = pd.DataFrame(records)

    # Format date
    df[TradeColumn.DATE.value] = pd.to_datetime(
        df["date"], errors="coerce"
    ).dt.strftime("%d/%m/%Y")
    custom_logger.debug("Formatted trade dates")

    # Convert numeric columns
    numeric_columns = [
        RawColumn.PRICE.value,
        RawColumn.COST.value,
        RawColumn.VOLUME.value,
        RawColumn.FEE.value,
    ]

    for col in numeric_columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(
            FormatRules.DECIMAL_PLACES_10
        )
        custom_logger.debug(f"Converted column to numeric: {col}")

    # Rename columns using RawColumn → TradeColumn mapping
    rename_map = {
        RawColumn.UID.value: TradeColumn.UNIQUE_ID.value,
        RawColumn.PAIR.value: TradeColumn.PAIR.value,
        RawColumn.TYPE.value: TradeColumn.TRADE_TYPE.value,
        RawColumn.SUBTYPE.value: TradeColumn.EXECUTION_TYPE.value,
        RawColumn.PRICE.value: TradeColumn.TRADE_PRICE.value,
        RawColumn.COST.value: TradeColumn.TRANSACTION_PRICE.value,
        RawColumn.VOLUME.value: TradeColumn.TRANSFERRED_VOLUME.value,
        RawColumn.FEE.value: TradeColumn.FEE.value,
    }

    df = df.rename(columns=rename_map)
    custom_logger.debug("Renamed columns to standardized format")

    # Extract currency and token from pair
    df[TradeColumn.CURRENCY.value] = df[TradeColumn.PAIR.value].str.extract(
        TradeRegex.PAIR_CURRENCY
    )
    df[TradeColumn.TOKEN.value] = df[TradeColumn.PAIR.value].str.extract(
        TradeRegex.PAIR_TOKEN
    )
    custom_logger.debug("Extracted currency and token from trading pair")

    # Final column order
    final_df = df[[col.value for col in TradeColumn]]
    custom_logger.info(f"✅ Trade DataFrame built with shape: {final_df.shape}")

    return final_df
