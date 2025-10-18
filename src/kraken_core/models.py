# =============================================================================
# 🏗️ Kraken Core Models
# =============================================================================
from dataclasses import dataclass
from typing import Optional

import pandas as pd


# -----------------------------------------------------------------------------
# 📈 Main Summary Metrics
# -----------------------------------------------------------------------------
@dataclass
class MainSummaryMetrics:
    """
    Aggregated summary metrics for a specific token/pair.

    Attributes:
        token: Quote token
        pair: Trading pair
        bought_volume: Total volume purchased
        sold_volume: Total volume sold
        remaining_volume: Volume still held
        average_buy_price: Weighted average buy price
        average_sell_price: Weighted average sell price (realized)
        market_price: Current market price
        total_cost: Total cost of purchases
        realized_sells: Total value from sells executed
        unrealized_value: Current value of remaining holdings
        total_value: Sum of realized_sells + unrealized_value
        roi: Realized ROI %
        if_all_sold_now_roi: ROI if fully sold now at current market price
    """

    token: str
    pair: str
    bought_volume: float
    sold_volume: float
    remaining_volume: float
    average_buy_price: float
    average_sell_price: float
    market_price: Optional[float]
    total_cost: float
    realized_sells: float
    unrealized_value: float
    total_value: float
    roi: float
    if_all_sold_now_roi: float


# -----------------------------------------------------------------------------
# 📉 Trade Breakdown Snapshot
# -----------------------------------------------------------------------------
@dataclass
class TradeBreakdownSnapshot:
    """
    Detailed breakdown of buys and sells for a specific token/pair.

    Attributes:
        pair: Trading pair
        buys: DataFrame of buy trades
        sells: DataFrame of sell trades
        market_price: Current market price
        currency: Base currency
        token: Quote token
        buy_volume: Total bought volume
        sell_volume: Total sold volume
        remaining_volume: Volume still held
        potential_value: Value if remaining holdings sold now
        sell_total: Total realized from sells
        current_value: Value of remaining holdings
    """

    pair: str
    buys: pd.DataFrame
    sells: pd.DataFrame
    market_price: Optional[float]
    currency: str
    token: str
    buy_volume: float
    sell_volume: float
    remaining_volume: float
    potential_value: float
    sell_total: float
    current_value: float
