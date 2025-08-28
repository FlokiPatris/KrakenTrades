# =============================================================================
# 🏗️ Kraken Core Models
# =============================================================================
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd


# -----------------------------------------------------------------------------
# 📊 Trade Record
# -----------------------------------------------------------------------------
@dataclass
class TradeRecord:
    """
    Represents a single executed trade.

    Attributes:
        unique_id: Unique identifier for the trade
        date: Execution datetime
        pair: Trading pair (e.g., BTC/USD)
        trade_type: 'Buy' or 'Sell'
        execution_type: 'Limit' or 'Market'
        trade_price: Price per unit
        transaction_price: Total value of this trade (price * volume)
        transferred_volume: Quantity bought or sold
        fee: Fee in base currency
        currency: Base currency
        token: Quote token
    """

    unique_id: str
    date: datetime
    pair: str
    trade_type: str
    execution_type: str
    trade_price: float
    transaction_price: float
    transferred_volume: float
    fee: float
    currency: str
    token: str


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
        total_cost: Total cost of purchases
        realized_sells: Total value from sells executed
        unrealized_value: Current value of remaining holdings
        total_value: Sum of realized_sells + unrealized_value
        roi: Realized ROI %
        potential_roi: ROI if fully sold now at current market price
    """

    token: str
    pair: str
    total_cost: float
    realized_sells: float
    unrealized_value: float
    total_value: float
    roi: float
    potential_roi: float


# -----------------------------------------------------------------------------
# 📊 Market Snapshot
# -----------------------------------------------------------------------------
@dataclass
class MarketSnapshot:
    """
    Snapshot of the market and positions at a given moment.

    Attributes:
        pair: Trading pair symbol
        market_price: Current market price for the pair
        buy_volume: Total bought volume
        sell_volume: Total sold volume
        remaining_volume: Volume still held
        buy_total: Total cost for buys
        sell_total: Total realized from sells
        cost: Current total cost of remaining holdings
        current_value: Current value of remaining holdings
        potential_value: Total potential value if fully sold now
        total_value: Sum of sell_total + current_value
        realized_roi: ROI based on realized sells
        potential_roi: ROI if all remaining holdings sold at market price
    """

    pair: str
    market_price: Optional[float] = None
    buy_volume: float = 0.0
    sell_volume: float = 0.0
    remaining_volume: float = 0.0
    buy_total: float = 0.0
    sell_total: float = 0.0
    cost: float = 0.0
    current_value: float = 0.0
    potential_value: float = 0.0
    total_value: float = 0.0
    realized_roi: float = 0.0
    potential_roi: float = 0.0


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
