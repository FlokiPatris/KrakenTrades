from enum import Enum


class TradeColumn(str, Enum):
    UNIQUE_ID = "Unique ID"
    DATE = "Date"
    PAIR = "Pair"
    TRADE_TYPE = "Trade Type"
    EXECUTION_TYPE = "Execution Type"
    TRADE_PRICE = "Trade Price"
    TRANSACTION_PRICE = "Transaction Price"
    TRANSFERRED_VOLUME = "Transferred Volume"
    FEE = "Fee"
    CURRENCY = "Currency"
    TOKEN = "Token"


class RawColumn(str, Enum):
    UID = "uid"
    DATE = "date"
    PAIR = "pair"
    TYPE = "type"
    SUBTYPE = "subtype"
    PRICE = "price"
    COST = "cost"
    VOLUME = "volume"
    FEE = "fee"
