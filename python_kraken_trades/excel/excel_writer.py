from python_kraken_trades.data_classes import MainSummaryMetrics, TradeBreakdownSnapshot
from python_kraken_trades.manual_injections import manual_onyx_injection, manual_litecoin_injection
from python_kraken_trades.market_data import fetch_market_price
from python_kraken_trades.enums import TradeColumn
from pathlib import Path
import pandas as pd


def generate_trade_report_block(title: str, values: dict) -> pd.DataFrame:
    """
    Creates a single-row DataFrame block with a title and associated values.
    Used for summary rows in the breakdown sheet.
    """
    return pd.DataFrame([{TradeColumn.UNIQUE_ID.value: title, **values}])


def generate_trade_report_sheet(snapshot: TradeBreakdownSnapshot) -> pd.DataFrame:
    """
    Generates a detailed breakdown sheet for a single trading pair,
    including Buys, Sells, and hypothetical value scenarios.
    """
    trade_summary_df = pd.concat([
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: "Buys"}]),
        snapshot.buys,
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: ""}]),
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: "Sells"}]),
        snapshot.sells,
        pd.DataFrame([{TradeColumn.UNIQUE_ID.value: ""}]),
        generate_trade_report_block("IF ALL SOLD NOW:", {
            TradeColumn.TRADE_PRICE.value: f"{snapshot.market_price:.4f} {snapshot.currency}" if snapshot.market_price else f"N/A {snapshot.currency}",
            TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.buy_volume:.4f} {snapshot.token}",
            TradeColumn.TRANSACTION_PRICE.value: f"{snapshot.potential_value:.4f} {snapshot.currency}" if snapshot.market_price else f"N/A {snapshot.currency}"
        }),
        generate_trade_report_block("ALREADY SOLD:", {
            TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.sell_volume:.4f} {snapshot.token}",
            TradeColumn.TRANSACTION_PRICE.value: f"{snapshot.sell_total:.4f} {snapshot.currency}"
        }),
        generate_trade_report_block("IF REST SOLD NOW:", {
            TradeColumn.TRANSFERRED_VOLUME.value: f"{snapshot.remaining_volume:.4f} {snapshot.token}",
            TradeColumn.TRANSACTION_PRICE.value: f"{snapshot.current_value:.4f} {snapshot.currency}" if snapshot.market_price else f"N/A {snapshot.currency}"
        })
    ], ignore_index=True).drop(columns=[TradeColumn.CURRENCY.value, TradeColumn.TOKEN.value])

    return trade_summary_df


def generate_portfolio_summary(
    total_buys: float,
    total_sells: float,
    unrealized_value: float,
    total_all_sold_now_value: float
) -> pd.DataFrame:
    """
    Creates a summary sheet for the entire portfolio, including net position and potential profit.
    """
    net_result = round((total_sells + unrealized_value - total_buys), 4)
    potential_profit = round(total_all_sold_now_value - total_buys, 4)

    summary = pd.DataFrame([
        ["Total Buys", round(total_buys, 4)],
        ["Total Sells", round(total_sells, 4)],
        ["Unrealized Value (if rest sold)", round(unrealized_value, 4)],
        ["If All Bought Sold Now (market value)", round(total_all_sold_now_value, 4)],
        ["Net Position", net_result],
        ["You Could Be Up To", f"{'🟢 You could be up to' if potential_profit >= 0 else '🔻 You could be down by'} €{abs(potential_profit):.4f}"],
        ["Result", f"{'🟢 You’re up' if net_result >= 0 else '🔻 You’re down'} €{abs(net_result):.4f}"]
    ], columns=["Metric", "EUR Value"])

    return summary


def export_roi_table(roi_records: list[MainSummaryMetrics], writer: pd.ExcelWriter) -> None:
    """
    Converts a list of MainSummaryMetrics into a sorted DataFrame and writes it to Excel.
    """
    roi_df = pd.DataFrame([r.__dict__ for r in roi_records]).sort_values("roi", ascending=True)
    roi_df.rename(columns={
        "total_cost": "Total Cost (€)",
        "realized_sells": "Realized Sells (€)",
        "unrealized_value": "Unrealized Value (€)",
        "total_value": "Total Value (€)",
        "roi": "ROI (%)",
        "potential_roi": "Potential ROI (%)"
    }, inplace=True)
    roi_df.to_excel(writer, sheet_name="Asset ROI", index=False)


# === CORE LOGIC ===
def write_excel(df: pd.DataFrame, output: Path) -> None:
    """
    Main function to generate an Excel report from trade data.
    Includes per-asset breakdowns, portfolio summary, and ROI analysis.
    """
    total_buys = 0.0
    total_sells = 0.0
    unrealized_value = 0.0
    total_all_sold_now_value = 0.0
    roi_records = []

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for pair, group in df.groupby(TradeColumn.PAIR.value):
            currency = group[TradeColumn.CURRENCY.value].iloc[0]
            token = group[TradeColumn.TOKEN.value].iloc[0]
            market_price = fetch_market_price(pair)

            buys = group[group[TradeColumn.TRADE_TYPE.value] == "Buy"].copy()
            sells = group[group[TradeColumn.TRADE_TYPE.value] == "Sell"].copy()

            if pair == "XCN/EUR":
                buys = manual_onyx_injection(buys)
            if pair == "LTC/EUR":
                buys = manual_litecoin_injection(buys)
            #TODO: Why just not pass only the number? And style in excel?
            def extract_amount(series: pd.Series) -> float:
                return series.str.extract(r"([\d.]+)").astype(float).sum()[0]

            buy_volume = extract_amount(buys[TradeColumn.TRANSFERRED_VOLUME.value])
            sell_volume = extract_amount(sells[TradeColumn.TRANSFERRED_VOLUME.value])
            buy_total = extract_amount(buys[TradeColumn.TRANSACTION_PRICE.value])
            buy_fee = extract_amount(buys[TradeColumn.FEE.value])
            sell_total = extract_amount(sells[TradeColumn.TRANSACTION_PRICE.value])
            remaining_volume = buy_volume - sell_volume

            cost = buy_total + buy_fee
            current_value = round(remaining_volume * market_price, 4) if market_price else 0
            potential_value = round(buy_volume * market_price, 4) if market_price else 0
            total_value = current_value + sell_total
            realized_roi = ((total_value - cost) / cost) if cost > 0 else 0
            potential_roi = ((potential_value - cost) / cost) if cost > 0 else 0

            total_buys += cost
            total_sells += sell_total
            unrealized_value += current_value
            total_all_sold_now_value += potential_value

            roi_records.append(MainSummaryMetrics(
                token=token,
                pair=pair,
                total_cost=round(cost, 2),
                realized_sells=round(sell_total, 2),
                unrealized_value=round(current_value, 2),
                total_value=round(total_value, 2),
                roi=round(realized_roi * 100, 2),
                potential_roi=round(potential_roi * 100, 2)
            ))

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
                current_value=current_value
            )

            sheet_name = pair.replace("/", "_")[:31]
            breakdown = generate_trade_report_sheet(snapshot)
            breakdown.to_excel(writer, sheet_name=sheet_name, index=False)

        summary = generate_portfolio_summary(
            total_buys=total_buys,
            total_sells=total_sells,
            unrealized_value=unrealized_value,
            total_all_sold_now_value=total_all_sold_now_value
        )
        summary.to_excel(writer, sheet_name="Portfolio", index=False)

        export_roi_table(roi_records, writer)