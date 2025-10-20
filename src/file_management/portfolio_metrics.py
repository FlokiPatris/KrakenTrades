# =============================================================================
# 🛠️ Portfolio Metrics & Trade Calculations
# =============================================================================
from typing import Optional

import pandas as pd

from kraken_core import (MainSummaryMetrics, MarketData, TradeColumn,
                         TradeMetricsResult, custom_logger)


def compute_trade_metrics(
    pair: str,
    group: pd.DataFrame,
    market_data: Optional[MarketData] = None,
) -> TradeMetricsResult:
    """
    Computes trade metrics and returns a TradeMetricsResult including
    MainSummaryMetrics with nested MarketData.
    """
    custom_logger.info(f"Computing metrics for pair: {pair}")

    if market_data is None:
        market_data = MarketData()  # fallback to empty

    # Split buys and sells
    buys = group[group[TradeColumn.TRADE_TYPE.value] == "Buy"].copy()
    sells = group[group[TradeColumn.TRADE_TYPE.value] == "Sell"].copy()

    # Aggregate volumes and totals
    buy_volume = buys[TradeColumn.TRANSFERRED_VOLUME.value].sum()
    sell_volume = sells[TradeColumn.TRANSFERRED_VOLUME.value].sum()
    buy_total = buys[TradeColumn.TRANSACTION_PRICE.value].sum()
    buy_fee = buys[TradeColumn.FEE.value].sum()
    sell_total = sells[TradeColumn.TRANSACTION_PRICE.value].sum()

    # Remaining holdings and costs
    remaining_volume = max(buy_volume - sell_volume, 0)
    cost = float(buy_total + buy_fee)
    market_price = market_data.price or 0.0
    current_value = remaining_volume * market_price
    potential_value = buy_volume * market_price
    total_value = current_value + sell_total

    # Average prices and ROI
    average_buy_price = (cost / buy_volume) if buy_volume else 0.0
    average_sell_price = (sell_total / sell_volume) if sell_volume else 0.0
    realized_roi = ((total_value - cost) / cost) if cost else 0.0
    potential_roi = ((potential_value - cost) / cost) if cost else 0.0

    # Create main summary metrics with nested MarketData
    metrics = MainSummaryMetrics(
        token=group[TradeColumn.TOKEN.value].iloc[0],
        bought_volume=buy_volume,
        sold_volume=sell_volume,
        remaining_volume=remaining_volume,
        average_buy_price=average_buy_price,
        average_sell_price=average_sell_price,
        market_price=market_price,
        total_cost=cost,
        realized_sells=sell_total,
        unrealized_value=current_value,
        total_value=total_value,
        roi=realized_roi * 100,
        if_all_sold_now_roi=potential_roi * 100,
        market_data=market_data,
    )

    return TradeMetricsResult(
        remaining_volume=remaining_volume,
        total_value=total_value,
        potential_value=potential_value,
        cost=cost,
        metrics=metrics,
    )


def generate_portfolio_summary(
    total_buys: float,
    total_sells: float,
    unrealized_value: float,
    total_all_sold_now_value: float,
) -> pd.DataFrame:
    """
    Summarizes the overall portfolio performance in a DataFrame.
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
