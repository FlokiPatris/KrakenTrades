from kraken_core import TradeRegex, FormatRules,TradeColumn, RawColumn
from pathlib import Path
from typing import List
import pandas as pd
import pdfplumber

def extract_kraken_trade_records_from_pdf(path: Path) -> List[dict]:
    records: List[dict] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")
            i = 0
            while i < len(lines) - 1:
                date_line = lines[i].strip()
                trade_line = lines[i + 1].strip()

                if TradeRegex.DATE.match(date_line) and not trade_line.startswith("Page"):
                    merged = f"{date_line} {trade_line}"
                    match = TradeRegex.TRADE.match(merged)
                    if match:
                        records.append(match.groupdict())
                    i += 2
                else:
                    i += 1

    if not records:
        raise RuntimeError("No trades matched — check PDF format or regex.")

    return records

def build_trade_dataframe(records: List[dict]) -> pd.DataFrame:
    df = pd.DataFrame(records)

    # Format date
    df[TradeColumn.DATE.value] = pd.to_datetime(df["date"], errors="coerce").dt.strftime("%d/%m/%Y")

    # Convert numeric columns
    for raw_col in [
        RawColumn.PRICE.value,
        RawColumn.COST.value,
        RawColumn.VOLUME.value,
        RawColumn.FEE.value
    ]:
        df[raw_col] = pd.to_numeric(df[raw_col], errors="coerce").round(FormatRules.ROUNDING_DECIMAL_PLACES)

    # Rename columns using RawColumn → TradeColumn mapping
    df = df.rename(columns={
        RawColumn.UID.value: TradeColumn.UNIQUE_ID.value,
        RawColumn.PAIR.value: TradeColumn.PAIR.value,
        RawColumn.TYPE.value: TradeColumn.TRADE_TYPE.value,
        RawColumn.SUBTYPE.value: TradeColumn.EXECUTION_TYPE.value,
        RawColumn.PRICE.value: TradeColumn.TRADE_PRICE.value,
        RawColumn.COST.value: TradeColumn.TRANSACTION_PRICE.value,
        RawColumn.VOLUME.value: TradeColumn.TRANSFERRED_VOLUME.value,
        RawColumn.FEE.value: TradeColumn.FEE.value
    })

    # Extract currency and token
    df[TradeColumn.CURRENCY.value] = df[TradeColumn.PAIR.value].str.extract(TradeRegex.PAIR_CURRENCY)
    df[TradeColumn.TOKEN.value] = df[TradeColumn.PAIR.value].str.extract(TradeRegex.PAIR_TOKEN)

    # Final column order
    return df[[col.value for col in TradeColumn]]