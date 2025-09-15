# =============================================================================
# 💾 Trade Excel / Export Module
# =============================================================================
from pathlib import Path
import pandas as pd

from kraken_core import (
    FormatRules,
    MainSummaryMetrics,
    TradeBreakdownSnapshot,
    TradeColumn,
    custom_logger,
)
from .trade_report_data import generate_trade_report_sheet, apply_manual_injections
from market import fetch_market_price


# -------------------------------------------------------------------------
# 🛠️ Portfolio & ROI Helpers
# -------------------------------------------------------------------------
def generate_portfolio_summary(
    total_buys: float,
    total_sells: float,
    unrealized_value: float,
    total_all_sold_now_value: float,
) -> pd.DataFrame:
    """
    Summarizes the overall portfolio performance.
    """
    custom_logger.info("Generating portfolio summary")

    net_result = round(total_sells + unrealized_value - total_buys)
    potential_profit = round(total_all_sold_now_value - total_buys)

    summary_data = [  # type:ignore
        ["Total Buys", round(total_buys)],
        ["Total Sells", round(total_sells)],
        ["Unrealized Value (if rest sold)", round(unrealized_value)],
        ["If All Bought Sold Now (market value)", round(total_all_sold_now_value)],
        ["Net Position", net_result],
        [
            "You Could Be Up To",
            f"{'🟢 You could be up to' if potential_profit >= 0 else '🔻 You could be down by'} €{abs(potential_profit)}",
        ],
        [
            "Result",
            f"{'🟢 You’re up' if net_result >= 0 else '🔻 You’re down'} €{abs(net_result)}",
        ],
    ]

    return pd.DataFrame(summary_data, columns=["Metric", "EUR Value"])


def export_roi_table(
    roi_records: list[MainSummaryMetrics], writer: pd.ExcelWriter
) -> None:
    """
    Writes the ROI summary table to the Excel writer.
    """
    custom_logger.info("Exporting ROI table")

    roi_df = pd.DataFrame([r.__dict__ for r in roi_records]).sort_values(  # type:ignore
        "roi", ascending=True
    )
    roi_df.rename(
        columns={
            "total_cost": "Total Cost (€)",
            "realized_sells": "Realized Sells (€)",
            "unrealized_value": "Unrealized Value (€)",
            "total_value": "Total Value (€)",
            "roi": "ROI (%)",
            "if_all_sold_now_roi": "If All Sold Now ROI (%)",
        },
        inplace=True,
    )

    roi_df.to_excel(writer, sheet_name="Asset ROI", index=False)  # type:ignore


# -------------------------------------------------------------------------
# 🖇️ Excel Writer
# -------------------------------------------------------------------------
def write_excel(df: pd.DataFrame, output: Path) -> None:
    """
    Processes trade data and writes a full Excel report including:
    - Individual token sheets
    - Portfolio summary
    - ROI table
    """
    custom_logger.info(f"📁 Writing Excel report to: {output}")

    total_buys = 0.0
    total_sells = 0.0
    unrealized_value = 0.0
    total_all_sold_now_value = 0.0
    roi_records: list[MainSummaryMetrics] = []

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for pair, group in df.groupby(TradeColumn.PAIR.value):  # type:ignore
            if not isinstance(pair, str):
                custom_logger.warning(f"Converting pair {pair} to string")
            pair_str = str(pair)
            custom_logger.info(f"📊 Processing pair: {pair}")

            currency = group[TradeColumn.CURRENCY.value].iloc[0]
            token = group[TradeColumn.TOKEN.value].iloc[0]
            market_price = fetch_market_price(pair_str)

            sells = group[group[TradeColumn.TRADE_TYPE.value] == "Sell"].copy()
            buys = group[group[TradeColumn.TRADE_TYPE.value] == "Buy"].copy()
            buys = apply_manual_injections(pair_str, buys)

            buy_volume = buys[TradeColumn.TRANSFERRED_VOLUME.value].sum()
            sell_volume = sells[TradeColumn.TRANSFERRED_VOLUME.value].sum()
            buy_total = buys[TradeColumn.TRANSACTION_PRICE.value].sum()
            buy_fee = buys[TradeColumn.FEE.value].sum()
            sell_total = sells[TradeColumn.TRANSACTION_PRICE.value].sum()

            remaining_volume = buy_volume - sell_volume

            if remaining_volume < 0.02 * buy_volume:
                custom_logger.info(
                    "Remaining volume is less than 2% of bought volume. Adjusting to zero."
                )
                remaining_volume = 0

            cost = float(buy_total + buy_fee)
            current_value = remaining_volume * market_price
            potential_value = buy_volume * market_price
            total_value = current_value + sell_total

            realized_roi = ((total_value - cost) / cost) if cost > 0 else 0
            potential_roi = ((potential_value - cost) / cost) if cost > 0 else 0

            total_buys += cost
            total_sells += sell_total
            unrealized_value += current_value
            total_all_sold_now_value += potential_value

            roi_records.append(
                MainSummaryMetrics(
                    token=token,
                    pair=pair_str,
                    total_cost=cost,
                    realized_sells=sell_total,
                    unrealized_value=current_value,
                    total_value=total_value,
                    roi=round(realized_roi * 100, FormatRules.DECIMAL_PLACES_8),
                    if_all_sold_now_roi=round(
                        potential_roi * 100, FormatRules.DECIMAL_PLACES_8
                    ),
                )
            )

            snapshot = TradeBreakdownSnapshot(
                pair=pair_str,
                buys=buys,
                sells=sells,
                market_price=market_price,
                currency=currency,
                token=token,
                buy_volume=buy_volume,
                sell_volume=sell_volume,
                remaining_volume=remaining_volume,
                potential_value=potential_value,
                sell_total=sell_total,
                current_value=current_value,
            )

            sheet_name = pair.replace("/", "_")[:31]  # type:ignore
            breakdown = generate_trade_report_sheet(snapshot)

            if breakdown.empty:
                breakdown = pd.DataFrame(
                    [{TradeColumn.UNIQUE_ID.value: "No trades available"}]
                )

            breakdown.to_excel(
                writer, sheet_name=sheet_name, index=False
            )  # type:ignore

        # Write Portfolio Summary
        summary = generate_portfolio_summary(
            total_buys=total_buys,
            total_sells=total_sells,
            unrealized_value=unrealized_value,
            total_all_sold_now_value=total_all_sold_now_value,
        )
        summary.to_excel(writer, sheet_name="Portfolio", index=False)  # type:ignore

        # Write ROI Table
        export_roi_table(roi_records, writer)

    custom_logger.info("✅ Excel report successfully written")
