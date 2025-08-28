# =============================================================================
# 📊 Trade DataFrame / Reporting Module
# =============================================================================
from typing import Optional, Any
import pandas as pd

from kraken_core import (
    TradeBreakdownSnapshot,
    TradeColumn,
    custom_logger,
)


# -------------------------------------------------------------------------
# 🛠️ Helper Functions
# -------------------------------------------------------------------------
def generate_trade_report_block(title: str, values: dict[str, Any]) -> pd.DataFrame:
    """
    Creates a single-row DataFrame with a title and associated trade metrics.
    """
    custom_logger.debug(f"Generating report block: {title}")
    return pd.DataFrame([{TradeColumn.UNIQUE_ID.value: title, **values}])


def create_summary_block(snapshot: TradeBreakdownSnapshot) -> list[pd.DataFrame]:
    """
    Generates all three standard summary blocks for a trade snapshot:
    - IF ALL SOLD NOW
    - ALREADY SOLD
    - IF REST SOLD NOW
    """

    def trade_price(val: Optional[float], currency: str) -> str:
        return f"{val} {currency}" if val is not None else f"N/A {currency}"

    return [
        generate_trade_report_block(
            "IF ALL SOLD NOW:",
            {
                TradeColumn.TRADE_PRICE.value: trade_price(
                    snapshot.market_price, snapshot.currency
                ),
                TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.buy_volume} {snapshot.token}",
                TradeColumn.TRANSACTION_PRICE.value: trade_price(
                    snapshot.potential_value, snapshot.currency
                ),
            },
        ),
        generate_trade_report_block(
            "ALREADY SOLD:",
            {
                TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.sell_volume} {snapshot.token}",
                TradeColumn.TRANSACTION_PRICE.value: f"{snapshot.sell_total} {snapshot.currency}",
            },
        ),
        generate_trade_report_block(
            "IF REST SOLD NOW:",
            {
                TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.remaining_volume} {snapshot.token}",
                TradeColumn.TRANSACTION_PRICE.value: trade_price(
                    snapshot.current_value, snapshot.currency
                ),
            },
        ),
    ]


def generate_trade_report_sheet(snapshot: TradeBreakdownSnapshot) -> pd.DataFrame:
    """
    Builds a full trade breakdown sheet from a snapshot of buys/sells and market data.
    """
    custom_logger.info(f"Generating trade sheet for: {snapshot.pair}")

    summary_blocks = [
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: "Buys"}]),
        snapshot.buys,
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: ""}]),
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: "Sells"}]),
        snapshot.sells,
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: ""}]),
        *create_summary_block(snapshot),
    ]

    report_df = pd.concat(summary_blocks, ignore_index=True)
    report_df.drop(
        columns=[TradeColumn.CURRENCY.value, TradeColumn.TOKEN.value],
        errors="ignore",
        inplace=True,
    )
    return report_df


def apply_manual_injections(pair: str, buys: pd.DataFrame) -> pd.DataFrame:
    """
    Applies manual corrections or injections to the 'buys' DataFrame based on the trading pair.
    """
    from market import manual_onyx_injection, manual_litecoin_injection

    custom_logger.debug(f"Applying manual injections for pair: {pair}")
    if pair == "XCN/EUR":
        return manual_onyx_injection(buys)
    elif pair == "LTC/EUR":
        return manual_litecoin_injection(buys)
    return buys
