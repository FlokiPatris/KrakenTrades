# --------------------------------------------------------------------
# 🧾 Kraken PDF Trade Parser
# --------------------------------------------------------------------
from pathlib import Path
from typing import List, Dict

import pandas as pd
import pdfplumber

from kraken_core import (
    FormatRules,
    RawColumn,
    TradeColumn,
    TradeRegex,
    custom_logger,
)


# --------------------------------------------------------------------
# 🛠 Helper Functions
# --------------------------------------------------------------------
def _extract_trade_lines_from_page(lines: List[str]) -> List[str]:
    """
    Merge date and trade lines for regex matching.
    """
    merged_lines: List[str] = []
    i = 0
    while i < len(lines) - 1:
        date_line = lines[i].strip()
        trade_line = lines[i + 1].strip()

        if TradeRegex.DATE.match(date_line) and not trade_line.startswith("Page"):
            merged_lines.append(f"{date_line} {trade_line}")
            i += 2
        else:
            i += 1
    return merged_lines


def _convert_numeric_columns(df: pd.DataFrame, columns: List[str]) -> pd.DataFrame:
    """
    Convert specified columns to numeric with fixed decimal places.
    """
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors="coerce").round(FormatRules.DECIMAL_PLACES_10)  # type: ignore
        custom_logger.debug(f"Converted column to numeric: {col}")
    return df


def _extract_currency_token(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract currency and token from trading pair column.
    """
    df[TradeColumn.CURRENCY.value] = df[TradeColumn.PAIR.value].str.extract(TradeRegex.PAIR_CURRENCY)  # type: ignore
    df[TradeColumn.TOKEN.value] = df[TradeColumn.PAIR.value].str.extract(TradeRegex.PAIR_TOKEN)  # type: ignore
    custom_logger.debug("Extracted currency and token from trading pair")
    return df


# --------------------------------------------------------------------
# 📄 PDF Trade Extractor
# --------------------------------------------------------------------
def extract_kraken_trade_records_from_pdf(path: Path) -> List[Dict[str, str]]:
    """
    Extracts Kraken trade records from a PDF file using regex patterns.

    Args:
        path (Path): Path to the Kraken trade PDF.

    Returns:
        List[Dict[str, str]]: List of raw trade records as dictionaries.

    Raises:
        FileNotFoundError: If the PDF does not exist.
        RuntimeError: If no trades could be extracted.
    """
    if not path.exists():
        raise FileNotFoundError(f"PDF file not found: {path}")

    custom_logger.info(f"📄 Starting PDF extraction from: {path}")
    records: List[Dict[str, str]] = []

    with pdfplumber.open(path) as pdf:
        custom_logger.debug(f"Opened PDF with {len(pdf.pages)} pages")

        for page_num, page in enumerate(pdf.pages, start=1):
            text = page.extract_text()
            if not text:
                continue
            lines = text.split("\n")
            custom_logger.debug(f"Page {page_num}: Extracted {len(lines)} lines")

            merged_lines = _extract_trade_lines_from_page(lines)

            for merged in merged_lines:
                match = TradeRegex.TRADE.match(merged)
                if match:
                    records.append(match.groupdict())
                    custom_logger.debug(f"Matched trade: {match.groupdict()}")
                else:
                    custom_logger.warning(f"Unmatched trade line: {merged}")

    if not records:
        custom_logger.error("No trades matched — check PDF format or regex.")
        raise RuntimeError("No trades matched — check PDF format or regex.")

    custom_logger.info(f"✅ Extracted {len(records)} trade records")
    return records


# --------------------------------------------------------------------
# 📊 Trade DataFrame Builder
# --------------------------------------------------------------------
def build_trade_dataframe(records: List[Dict[str, str]]) -> pd.DataFrame:
    """
    Converts raw trade records into a formatted DataFrame with standardized columns.

    Args:
        records (List[Dict[str, str]]): List of raw trade records.

    Returns:
        pd.DataFrame: Formatted DataFrame with standardized trade columns.
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
    df = _convert_numeric_columns(df, numeric_columns)

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

    # Extract currency and token
    df = _extract_currency_token(df)

    # Final column order
    final_df = df[[col.value for col in TradeColumn]]
    custom_logger.info(f"✅ Trade DataFrame built with shape: {final_df.shape}")

    return final_df
