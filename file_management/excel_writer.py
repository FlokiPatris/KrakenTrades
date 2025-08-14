from kraken_core import (
    MainSummaryMetrics,
    TradeBreakdownSnapshot,
    TradeColumn,
    FormatRules,
    custom_logger,
)
from market import manual_onyx_injection, manual_litecoin_injection, fetch_market_price
from pathlib import Path
import pandas as pd


# === Report Block Generator ===
def generate_trade_report_block(title: str, values: dict) -> pd.DataFrame:
    """
    Creates a single-row DataFrame with a title and associated trade metrics.
    """
    custom_logger.debug(f"Generating report block: {title}")
    return pd.DataFrame([{TradeColumn.UNIQUE_ID.value: title, **values}])


# === Trade Sheet Generator ===
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
        generate_trade_report_block(
            "IF ALL SOLD NOW:",
            {
                TradeColumn.TRADE_PRICE.value: (
                    f"{snapshot.market_price} {snapshot.currency}"
                    if snapshot.market_price
                    else f"N/A {snapshot.currency}"
                ),
                TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.buy_volume} {snapshot.token}",
                TradeColumn.TRANSACTION_PRICE.value: (
                    f"{snapshot.potential_value} {snapshot.currency}"
                    if snapshot.market_price
                    else f"N/A {snapshot.currency}"
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
                TradeColumn.TRANSACTION_PRICE.value: (
                    f"{snapshot.current_value} {snapshot.currency}"
                    if snapshot.market_price
                    else f"N/A {snapshot.currency}"
                ),
            },
        ),
    ]

    report_df = pd.concat(summary_blocks, ignore_index=True)
    report_df.drop(
        columns=[TradeColumn.CURRENCY.value, TradeColumn.TOKEN.value],
        errors="ignore",
        inplace=True,
    )

    return report_df


# === Portfolio Summary Generator ===
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

    summary_data = [
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


# === ROI Exporter ===
def export_roi_table(
    roi_records: list[MainSummaryMetrics], writer: pd.ExcelWriter
) -> None:
    """
    Writes the ROI summary table to the Excel writer.
    """
    custom_logger.info("Exporting ROI table")

    roi_df = pd.DataFrame([r.__dict__ for r in roi_records]).sort_values(
        "roi", ascending=True
    )
    roi_df.rename(
        columns={
            "total_cost": "Total Cost (€)",
            "realized_sells": "Realized Sells (€)",
            "unrealized_value": "Unrealized Value (€)",
            "total_value": "Total Value (€)",
            "roi": "ROI (%)",
            "potential_roi": "Potential ROI (%)",
        },
        inplace=True,
    )

    roi_df.to_excel(writer, sheet_name="Asset ROI", index=False)


# === Manual Injection Handler ===
def apply_manual_injections(pair: str, buys: pd.DataFrame) -> pd.DataFrame:
    """
    Applies manual corrections or injections to the 'buys' DataFrame based on the trading pair.
    """
    custom_logger.debug(f"Applying manual injections for pair: {pair}")
    if pair == "XCN/EUR":
        buys = manual_onyx_injection(buys)
    elif pair == "LTC/EUR":
        buys = manual_litecoin_injection(buys)
    return buys


# === Excel Writer ===
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
        for pair, group in df.groupby(TradeColumn.PAIR.value):
            custom_logger.info(f"📊 Processing pair: {pair}")

            currency = group[TradeColumn.CURRENCY.value].iloc[0]
            token = group[TradeColumn.TOKEN.value].iloc[0]
            market_price = fetch_market_price(pair)

            sells = group[group[TradeColumn.TRADE_TYPE.value] == "Sell"].copy()
            buys = group[group[TradeColumn.TRADE_TYPE.value] == "Buy"].copy()
            buys = apply_manual_injections(pair, buys)

            buy_volume = buys[TradeColumn.TRANSFERRED_VOLUME.value].sum()
            sell_volume = sells[TradeColumn.TRANSFERRED_VOLUME.value].sum()
            buy_total = buys[TradeColumn.TRANSACTION_PRICE.value].sum()
            buy_fee = buys[TradeColumn.FEE.value].sum()
            sell_total = sells[TradeColumn.TRANSACTION_PRICE.value].sum()

            remaining_volume = buy_volume - sell_volume
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
                    pair=pair,
                    total_cost=cost,
                    realized_sells=sell_total,
                    unrealized_value=current_value,
                    total_value=total_value,
                    roi=round(realized_roi * 100, FormatRules.DECIMAL_PLACES_8),
                    potential_roi=round(
                        potential_roi * 100, FormatRules.DECIMAL_PLACES_8
                    ),
                )
            )

            snapshot = TradeBreakdownSnapshot(
                pair=pair,
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

            sheet_name = pair.replace("/", "_")[:31]
            breakdown = generate_trade_report_sheet(snapshot)

            if breakdown.empty:
                breakdown = pd.DataFrame(
                    [{TradeColumn.UNIQUE_ID.value: "No trades available"}]
                )

            breakdown.to_excel(writer, sheet_name=sheet_name, index=False)

        # Write Portfolio Summary
        summary = generate_portfolio_summary(
            total_buys=total_buys,
            total_sells=total_sells,
            unrealized_value=unrealized_value,
            total_all_sold_now_value=total_all_sold_now_value,
        )
        summary.to_excel(writer, sheet_name="Portfolio", index=False)

        # Write ROI Table
        export_roi_table(roi_records, writer)

    custom_logger.info("✅ Excel report successfully written")
