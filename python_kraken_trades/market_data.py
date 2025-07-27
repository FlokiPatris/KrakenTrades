from typing import Optional
from constants import KrakenAPI
import requests

# === MARKET PRICE FETCHING ===
def fetch_market_price(pair: str) -> Optional[float]:
    """
    Fetches the current market price for a given trading pair from Kraken API.
    """
    code = pair.replace("/", "").replace("BTC", "XBT")
    try:
        response = requests.get(
            KrakenAPI.URL,
            params={"pair": code},
            timeout=KrakenAPI.TIMEOUT,
        )
        response.raise_for_status()
        data = next(iter(response.json().get("result", {}).values()), {})
        return float(data.get("c", [None])[0])
    except Exception:
        return None