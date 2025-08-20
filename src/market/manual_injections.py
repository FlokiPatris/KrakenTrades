import pandas as pd

from src.kraken_core import TradeColumn


# === MANUAL INJECTIONS ===
def manual_onyx_injection(buys: pd.DataFrame) -> pd.DataFrame:
    manual_buy = pd.DataFrame(
        [
            {
                TradeColumn.UNIQUE_ID: "MANUAL-ONYX-BUY",
                TradeColumn.DATE: "15/03/2025",
                TradeColumn.PAIR: "XCN/EUR",
                TradeColumn.TRADE_TYPE: "Buy",
                TradeColumn.EXECUTION_TYPE: "Market",
                TradeColumn.TRADE_PRICE: 0.1212,
                TradeColumn.TRANSACTION_PRICE: 640.0,
                TradeColumn.TRANSFERRED_VOLUME: 47349.9627,
                TradeColumn.FEE: 30.0,
                TradeColumn.CURRENCY: "EUR",
                TradeColumn.TOKEN: "XCN",
            }
        ]
    )

    return pd.concat([buys, manual_buy], ignore_index=True)


def manual_litecoin_injection(buys: pd.DataFrame) -> pd.DataFrame:
    manual_buy = pd.DataFrame(
        [
            {
                TradeColumn.UNIQUE_ID: "MANUAL-LTC-BUY",
                TradeColumn.DATE: "21/07/2025",
                TradeColumn.PAIR: "LTC/EUR",
                TradeColumn.TRADE_TYPE: "Buy",
                TradeColumn.EXECUTION_TYPE: "Market",
                TradeColumn.TRADE_PRICE: 94.4,
                TradeColumn.TRANSACTION_PRICE: 16.34,
                TradeColumn.TRANSFERRED_VOLUME: 0.16568818,
                TradeColumn.FEE: 0.0,
                TradeColumn.CURRENCY: "EUR",
                TradeColumn.TOKEN: "LTC",
            }
        ]
    )

    return pd.concat([buys, manual_buy], ignore_index=True)
