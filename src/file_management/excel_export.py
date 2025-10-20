from __future__ import annotations

from pathlib import Path
from typing import List
import pandas as pd

from kraken_core import (
    TradeColumn,
    custom_logger,
    TradeBreakdownSnapshot,
    TradeMetricsResult,
    TOKEN_MAP,
)
from market.market_data import fetch_bulk_market_data
from .portfolio_metrics import compute_trade_metrics, generate_portfolio_summary
from .trade_report_data import apply_manual_injections, generate_trade_report_sheet


# =============================================================================
# 📊 ROI Table Writer
# =============================================================================
def write_roi_table(roi_records: List[TradeMetricsResult], writer: pd.ExcelWriter) -> None:
    """Writes ROI summary table including extended metrics to Excel."""
    custom_logger.info("Exporting ROI table with extended market metrics")

    if not roi_records:
        custom_logger.warning("⚠️ No ROI records found — skipping ROI table.")
        empty_df = pd.DataFrame([{"Notice": "No ROI data available"}])
        empty_df.to_excel(writer, sheet_name="Asset ROI", index=False)
        return

    # Flatten TradeMetricsResult (includes MainSummaryMetrics + MarketData)
    from .excel_styler import flatten_trade_metrics_result  # ensures latest version used
    flat_data = [flatten_trade_metrics_result(r) for r in roi_records]

    roi_df = pd.DataFrame(flat_data)

    if "roi" not in roi_df.columns:
        custom_logger.error("❌ Missing 'roi' in ROI DataFrame columns")
        roi_df.to_excel(writer, sheet_name="Asset ROI", index=False)
        return

    roi_df = roi_df.sort_values("roi", ascending=True)

    # Rename columns for readability
    columns_map = {
        "token": "Token",
        "bought_volume": "Bought Volume",
        "sold_volume": "Sold Volume",
        "remaining_volume": "Remaining Volume",
        "average_buy_price": "Avg Buy Price (€)",
        "average_sell_price": "Avg Sell Price (€)",
        "market_price": "Current Market Price (€)",
        "total_cost": "Total Cost (€)",
        "realized_sells": "Realized Sells (€)",
        "unrealized_value": "Unrealized Value (€)",
        "total_value": "Total Value (€)",
        "roi": "ROI (%)",
        "if_all_sold_now_roi": "If All Sold Now ROI (%)",
        "market_cap": "Market Cap (€)",
        "daily_volume": "24h Volume (€)",
        "volatility_30d": "30d Volatility (%)",
        "momentum_30d": "30d Momentum (%)",
        "dominance": "Dominance (%)",
        "high_24h": "24h High (€)",
        "low_24h": "24h Low (€)",
        "price_change_24h": "Price Change 24h (€)",
        "price_change_percentage_24h": "Price Change 24h (%)",
        "market_cap_change_percentage_24h": "Market Cap Change 24h (%)",
        "ath": "All-Time High (€)",
        "ath_change_percentage": "ATH Change (%)",
        "ath_date": "ATH Date",
    }
    roi_df.rename(columns=columns_map, inplace=True)
    roi_df.to_excel(writer, sheet_name="Asset ROI", index=False)


# =============================================================================
# 🧾 Token Sheet Writer
# =============================================================================
def write_token_sheet(snapshot: TradeBreakdownSnapshot, writer: pd.ExcelWriter) -> None:
    """Writes an individual token sheet to Excel."""
    sheet_name = snapshot.pair.replace("/", "_")[:31]
    breakdown = generate_trade_report_sheet(snapshot)
    if breakdown.empty:
        breakdown = pd.DataFrame([{TradeColumn.UNIQUE_ID.value: "No trades available"}])
    breakdown.to_excel(writer, sheet_name=sheet_name, index=False)


# =============================================================================
# 💰 Portfolio Report Writer
# =============================================================================
def write_portfolio_report(df: pd.DataFrame, output: Path) -> None:
    """
    Main Excel writer function.
    Generates individual token sheets, portfolio summary, and ROI table.
    """
    custom_logger.info(f"📁 Writing Excel report to: {output}")

    total_buys_sum = 0.0
    total_sells_sum = 0.0
    unrealized_value_sum = 0.0
    total_all_sold_now_value_sum = 0.0
    roi_records: List[TradeMetricsResult] = []

    pairs = df[TradeColumn.PAIR.value].dropna().unique().tolist()
    market_data_map = fetch_bulk_market_data(pairs, TOKEN_MAP)

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for pair, group in df.groupby(TradeColumn.PAIR.value):
            pair_str = str(pair)
            custom_logger.info(f"📊 Processing pair: {pair_str}")

            currency = group[TradeColumn.CURRENCY.value].iloc[0]
            token = group[TradeColumn.TOKEN.value].iloc[0]

            group = apply_manual_injections(pair_str, group)

            # Compute metrics
            metrics_result = compute_trade_metrics(pair_str, group, market_data_map.get(pair_str, {}))
            metrics = metrics_result.metrics

            # Aggregate totals
            total_buys_sum += metrics_result.cost
            total_sells_sum += metrics.realized_sells
            unrealized_value_sum += metrics.unrealized_value
            total_all_sold_now_value_sum += metrics_result.potential_value

            # Add to ROI records
            roi_records.append(metrics_result)

            # Token sheet
            snapshot = TradeBreakdownSnapshot(
                pair=pair_str,
                buys=group[group[TradeColumn.TRADE_TYPE.value] == "Buy"],
                sells=group[group[TradeColumn.TRADE_TYPE.value] == "Sell"],
                market_price=metrics.market_price,
                currency=currency,
                token=token,
                buy_volume=metrics.bought_volume,
                sell_volume=metrics.sold_volume,
                remaining_volume=metrics.remaining_volume,
                potential_value=metrics_result.potential_value,
                sell_total=metrics.realized_sells,
                current_value=metrics.unrealized_value,
            )
            write_token_sheet(snapshot, writer)

        # Portfolio summary
        summary_df = generate_portfolio_summary(
            total_buys=total_buys_sum,
            total_sells=total_sells_sum,
            unrealized_value=unrealized_value_sum,
            total_all_sold_now_value=total_all_sold_now_value_sum,
        )
        summary_df.to_excel(writer, sheet_name="Portfolio", index=False)

        # ROI table (handles empty or missing data safely)
        write_roi_table(roi_records, writer)

    custom_logger.info("✅ Excel report successfully written")
