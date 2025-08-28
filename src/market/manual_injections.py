import pandas as pd

from kraken_core import TradeColumn


# === MANUAL INJECTIONS ===
# NOTE: Values below are anonymized.
def manual_onyx_injection(buys: pd.DataFrame) -> pd.DataFrame:
    manual_buy = pd.DataFrame(
        [
            {
                TradeColumn.UNIQUE_ID: "MANUAL-ONYX-BUY",
                TradeColumn.DATE: "12/03/2025",
                TradeColumn.PAIR: "XCN/EUR",
                TradeColumn.TRADE_TYPE: "Buy",
                TradeColumn.EXECUTION_TYPE: "Market",
                TradeColumn.TRADE_PRICE: 0.1210,
                TradeColumn.TRANSACTION_PRICE: 640.0,
                TradeColumn.TRANSFERRED_VOLUME: 47339.9627,
                TradeColumn.FEE: 30.0,
                TradeColumn.CURRENCY: "EUR",
                TradeColumn.TOKEN: "XCN",
            }
        ]
    )

    return pd.concat([buys, manual_buy], ignore_index=True)


# NOTE: Values below are anonymized.
def manual_litecoin_injection(buys: pd.DataFrame) -> pd.DataFrame:
    manual_buy = pd.DataFrame(
        [
            {
                TradeColumn.UNIQUE_ID: "MANUAL-LTC-BUY",
                TradeColumn.DATE: "20/07/2025",
                TradeColumn.PAIR: "LTC/EUR",
                TradeColumn.TRADE_TYPE: "Buy",
                TradeColumn.EXECUTION_TYPE: "Market",
                TradeColumn.TRADE_PRICE: 93.8,
                TradeColumn.TRANSACTION_PRICE: 16.32,
                TradeColumn.TRANSFERRED_VOLUME: 0.16468818,
                TradeColumn.FEE: 0.0,
                TradeColumn.CURRENCY: "EUR",
                TradeColumn.TOKEN: "LTC",
            }
        ]
    )

    return pd.concat([buys, manual_buy], ignore_index=True)
