# =============================================================================
# 🧩 Imports
# =============================================================================
from typing import Optional

import requests

from kraken_core import KrakenAPI, custom_logger


# =============================================================================
# 🛠️ Helper Functions
# =============================================================================
def _format_pair_code(pair: str) -> str:
    """
    Converts a trading pair into Kraken API format.
    E.g., "BTC/USD" -> "XBTUSD"
    """
    return pair.replace("/", "").replace("BTC", "XBT")


# =============================================================================
# 💹 Market Data Fetcher
# =============================================================================
def fetch_market_price(pair: str) -> Optional[float]:
    """
    Fetches the current market price for a given trading pair from Kraken API.
    Logs request status and errors using the custom logger.

    Returns:
        float: The current market price, or None if an error occurred.
    """
    code = _format_pair_code(pair)
    custom_logger.info(f"Fetching market price for pair: {pair} (API code: {code})")

    try:
        response = requests.get(
            KrakenAPI.URL,
            params={"pair": code},
            timeout=KrakenAPI.TIMEOUT,
        )
        response.raise_for_status()
        custom_logger.debug(f"Raw response: {response.text[:200]}...")  # truncated

        result = response.json().get("result", {})
        if not result:
            custom_logger.warning(f"No result found in API response for {pair}")
            return None

        data = next(iter(result.values()))
        price_str = data.get("c", [None])[0]

        if price_str is None:
            custom_logger.warning(f"No closing price found for {pair}")
            return None

        price = float(price_str)
        custom_logger.info(f"Market price for {pair}: {price}")
        return price

    except requests.exceptions.RequestException as req_err:
        custom_logger.warning(f"Request error while fetching {pair}: {req_err}")
    except (ValueError, TypeError) as parse_err:
        custom_logger.warning(f"Parsing error for {pair} response: {parse_err}")

    # None is returned on any handled error
    return None
