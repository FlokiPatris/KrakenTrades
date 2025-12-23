from dataclasses import dataclass
from typing import Optional

import pandas as pd


# -----------------------------------------------------------------------------
# 📊 Market Data for a Token (CoinGecko + Kraken)
# -----------------------------------------------------------------------------
@dataclass
class MarketData:
    price: Optional[float] = None
    daily_volume: Optional[float] = None
    market_cap: Optional[float] = None
    volatility_30d: Optional[float] = None
    momentum_30d: Optional[float] = None
    dominance: Optional[float] = None
    high_24h: Optional[float] = None
    low_24h: Optional[float] = None
    price_change_percentage_24h: Optional[float] = None
    market_cap_change_percentage_24h: Optional[float] = None
    ath: Optional[float] = None
    ath_change_percentage: Optional[float] = None
    ath_date: Optional[str] = None


# -----------------------------------------------------------------------------
# 📈 Main Summary Metrics (Extended with Market Data)
# -----------------------------------------------------------------------------
@dataclass
class MainSummaryMetrics:
    """
    Aggregated summary metrics for a specific token/pair.

    Attributes:
        token: Quote token
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
        market_data: Nested MarketData containing CoinGecko/Kraken metrics
    """

    token: str
    bought_volume: float
    sold_volume: float
    remaining_volume: float
    average_buy_price: float
    average_sell_price: float
    market_price: Optional[float]
    total_cost: float
    realized_sells_eur: float
    realized_sells_czk: float
    unrealized_value: float
    total_value: float
    roi: float
    if_all_sold_now_roi: float
    
    # 🔹 Nested Market Data
    market_data: Optional[MarketData] = None


# -----------------------------------------------------------------------------
# 📉 Trade Breakdown Snapshot
# -----------------------------------------------------------------------------
@dataclass
class TradeBreakdownSnapshot:
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
    sell_total_eur: float
    current_value: float


# -----------------------------------------------------------------------------
# 🧮 Trade Metrics Result
# -----------------------------------------------------------------------------
@dataclass
class TradeMetricsResult:
    remaining_volume: float
    total_value: float
    potential_value: float
    cost: float
    metrics: MainSummaryMetrics
