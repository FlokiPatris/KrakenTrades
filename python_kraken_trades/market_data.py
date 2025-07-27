from typing import Optional
import requests
import pandas as pd

from enums import TradeColumn

# === MARKET PRICE FETCHING ===
def fetch_market_price(pair: str) -> Optional[float]:
    """
    Fetches the current market price for a given trading pair from Kraken API.
    """
    code = pair.replace("/", "").replace("BTC", "XBT")
    try:
        response = requests.get(
            "https://api.kraken.com/0/public/Ticker",
            params={"pair": code},
            timeout=10
        )
        response.raise_for_status()
        data = next(iter(response.json().get("result", {}).values()), {})
        return float(data.get("c", [None])[0])
    except Exception:
        return None
    return pd.concat([buys, manual_buy], ignore_index=True)