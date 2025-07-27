from kraken_core import KrakenAPI, custom_logger
from typing import Optional
import requests

def fetch_market_price(pair: str) -> Optional[float]:
    """
    Fetches the current market price for a given trading pair from Kraken API.
    Logs request status and errors using the custom logger.
    """
    code = pair.replace("/", "").replace("BTC", "XBT")
    custom_logger.info(f"Fetching market price for pair: {pair} (API code: {code})")

    try:
        response = requests.get(
            KrakenAPI.URL,
            params={"pair": code},
            timeout=KrakenAPI.TIMEOUT,
        )
        response.raise_for_status()
        custom_logger.debug(f"Raw response: {response.text[:200]}...")  # Optional: truncate for readability

        data = next(iter(response.json().get("result", {}).values()), {})
        price = float(data.get("c", [None])[0])
        custom_logger.info(f"Market price for {pair}: {price}")
        return price

    except requests.exceptions.RequestException as req_err:
        custom_logger.warning(f"Request error while fetching {pair}: {req_err}")
    except (ValueError, TypeError) as parse_err:
        custom_logger.warning(f"Parsing error for {pair} response: {parse_err}")
    except Exception as e:
        custom_logger.exception(f"Unexpected error while fetching market price for {pair}")

    return None