from constants import DATE_RE, TRADE_RE
from enums import TradeColumn, RawColumn
from pathlib import Path
from typing import List
import pandas as pd
import pdfplumber

# === PARSING ===
def parse_pdf(path: Path) -> pd.DataFrame:
    records: List[dict] = []

    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            lines = page.extract_text().split("\n")
            i = 0
            while i < len(lines) - 1:
                date_line = lines[i].strip()
                trade_line = lines[i + 1].strip()

                if DATE_RE.match(date_line) and not trade_line.startswith("Page"):
                    merged = f"{date_line} {trade_line}"
                    match = TRADE_RE.match(merged)
                    if match:
                        record = match.groupdict()
                        records.append(record)
                    i += 2
                else:
                    i += 1

    if not records:
        raise RuntimeError("No trades matched — check PDF format or regex.")

    data_frame = pd.DataFrame(records)

    # Format date
    data_frame[TradeColumn.DATE.value] = pd.to_datetime(data_frame["date"], errors="coerce").dt.strftime("%d/%m/%Y")

    # Convert numeric columns
    for raw_col in [
        RawColumn.PRICE.value,
        RawColumn.COST.value,
        RawColumn.VOLUME.value,
        RawColumn.FEE.value
    ]:
        data_frame[raw_col] = pd.to_numeric(data_frame[raw_col], errors="coerce").round(4)

    # Rename columns using RawColumn → TradeColumn mapping
    data_frame = data_frame.rename(columns={
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
    data_frame[TradeColumn.CURRENCY.value] = data_frame[TradeColumn.PAIR.value].str.extract(r"/([A-Z]+)")
    data_frame[TradeColumn.TOKEN.value] = data_frame[TradeColumn.PAIR.value].str.extract(r"^([A-Z0-9]+)/")

    # Format fields with units
    data_frame[TradeColumn.TRANSACTION_PRICE.value] = data_frame[TradeColumn.TRANSACTION_PRICE.value].astype(str) + " " + data_frame[TradeColumn.CURRENCY.value]
    data_frame[TradeColumn.TRADE_PRICE.value] = data_frame[TradeColumn.TRADE_PRICE.value].astype(str) + " " + data_frame[TradeColumn.CURRENCY.value]
    data_frame[TradeColumn.FEE.value] = data_frame[TradeColumn.FEE.value].astype(str) + " " + data_frame[TradeColumn.CURRENCY.value]
    data_frame[TradeColumn.TRANSFERRED_VOLUME.value] = data_frame[TradeColumn.TRANSFERRED_VOLUME.value].astype(str) + " " + data_frame[TradeColumn.TOKEN.value]

    # Final column order
    return data_frame[[col.value for col in TradeColumn]]