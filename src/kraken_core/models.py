# models.py
from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import pandas as pd


@dataclass
class TradeRecord:
    unique_id: str
    date: datetime
    pair: str
    trade_type: str  # Buy or Sell
    execution_type: str  # Limit or Market
    trade_price: float
    transaction_price: float
    transferred_volume: float
    fee: float
    currency: str
    token: str


@dataclass
class MainSummaryMetrics:
    token: str
    pair: str
    total_cost: float
    realized_sells: float
    unrealized_value: float
    total_value: float
    roi: float  # Realized ROI %
    potential_roi: float  # ROI if fully sold now %


@dataclass
class MarketSnapshot:
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
    sell_total: float
    current_value: float
