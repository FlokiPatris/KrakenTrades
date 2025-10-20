from typing import  Dict, List
import requests
import numpy as np
from urllib3 import Retry
from kraken_core import KrakenAPI, custom_logger, MarketData
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

COINGECKO_API = "https://api.coingecko.com/api/v3"

# =========================
# Requests session with retries
# =========================
session = requests.Session()
retries = Retry(
    total=3,
    backoff_factor=1,
    status_forcelist=[429, 500, 502, 503, 504],
    allowed_methods=["GET"]
)
adapter = HTTPAdapter(max_retries=retries)
session.mount("https://", adapter)
session.mount("http://", adapter)

# =========================
# Utilities
# =========================
def _format_pair_code(pair: str) -> str:
    return pair.replace("/", "").replace("BTC", "XBT")

DOMINANCE_MAPPING = {
    "steth": "steth",
    "usdt": "usdt",
    "usdc": "usdc",
    "bnb": "bnb",
    "solana": "sol",
    "cardano": "ada",
    "bitcoin": "btc",
    "ethereum": "eth",
    "chainlink": "link",
    "ripple": "xrp",
    "fetch-ai": "fet",
}

# =========================
# Global dominance caching
# =========================
_global_dominance_cache: Dict[str, float] = {}

def fetch_global_dominance() -> Dict[str, float]:
    global _global_dominance_cache
    if _global_dominance_cache:
        return _global_dominance_cache
    try:
        resp = session.get(f"{COINGECKO_API}/global", timeout=10)
        resp.raise_for_status()
        _global_dominance_cache = resp.json()["data"]["market_cap_percentage"]
    except Exception as e:
        custom_logger.warning(f"Failed to fetch global dominance: {e}")
        _global_dominance_cache = {}
    return _global_dominance_cache

def fetch_coin_dominance(token_id: str) -> float:
    key = DOMINANCE_MAPPING.get(token_id.lower())
    if not key:
        return 0.0
    dominance_data = fetch_global_dominance()
    return float(dominance_data.get(key, 0))

# =========================
# Fetch historical prices (30d)
# =========================
def fetch_historical_prices(token_id: str, vs_currency: str = "eur", days: int = 30) -> List[float]:
    try:
        resp = session.get(
            f"{COINGECKO_API}/coins/{token_id}/market_chart",
            params={"vs_currency": vs_currency, "days": days},
            timeout=10
        )
        resp.raise_for_status()
        return [price[1] for price in resp.json().get("prices", [])]
    except Exception as e:
        custom_logger.warning(f"Failed to fetch 30d prices for {token_id}: {e}")
        return []

def calculate_volatility_momentum(prices: List[float]) -> (float, float):
    if len(prices) < 2:
        return 0.0, 0.0
    returns = np.diff(prices) / prices[:-1]
    volatility = float(np.std(returns) * 100)
    momentum = float((prices[-1] - prices[0]) / prices[0] * 100)
    return volatility, momentum

# =========================
# Fetch CoinGecko bulk market data
# =========================
def fetch_coingecko_data_bulk(token_ids: List[str], vs_currency: str = "eur") -> Dict[str, MarketData]:
    md_map: Dict[str, MarketData] = {}
    try:
        ids = ",".join(token_ids)
        resp = session.get(f"{COINGECKO_API}/coins/markets", params={"vs_currency": vs_currency, "ids": ids}, timeout=10)
        resp.raise_for_status()
        data_list = resp.json()

        for data in data_list:
            md = MarketData()
            md.market_cap = float(data.get("market_cap", 0))
            md.high_24h = float(data.get("high_24h", 0))
            md.low_24h = float(data.get("low_24h", 0))
            md.price_change_percentage_24h = float(data.get("price_change_percentage_24h", 0))
            md.market_cap_change_percentage_24h = float(data.get("market_cap_change_percentage_24h", 0))
            md.ath = float(data.get("ath", 0))
            md.ath_change_percentage = float(data.get("ath_change_percentage", 0))
            md.ath_date = data.get("ath_date")
            md.dominance = fetch_coin_dominance(data["id"])

            # 30d metrics
            prices_30d = fetch_historical_prices(data["id"])
            md.volatility_30d, md.momentum_30d = calculate_volatility_momentum(prices_30d)

            md_map[data["id"]] = md

    except Exception as e:
        custom_logger.warning(f"Failed bulk CoinGecko fetch: {e}")
    return md_map

# =========================
# Fetch Kraken data per pair
# =========================
def fetch_kraken_data(pair: str) -> dict:
    code = _format_pair_code(pair)
    try:
        resp = session.get(KrakenAPI.URL, params={"pair": code}, timeout=KrakenAPI.TIMEOUT)
        resp.raise_for_status()
        kraken_data = resp.json().get("result", {})
        if kraken_data:
            pair_data = next(iter(kraken_data.values()))
            return {
                "price": float(pair_data.get("c", [0])[0]),
                "daily_volume": float(pair_data.get("v", [0, 0])[1])
            }
    except Exception as e:
        custom_logger.warning(f"Kraken fetch failed for {pair}: {e}")
    return {"price": None, "daily_volume": None}

# =========================
# Combine Kraken + CoinGecko + 30d metrics
# =========================
def fetch_market_data(pair: str, token_id: str, cg_map: Dict[str, MarketData]) -> MarketData:
    md = cg_map.get(token_id, MarketData())
    kraken_data = fetch_kraken_data(pair)
    if kraken_data["price"] is not None:
        md.price = kraken_data["price"]
    if kraken_data["daily_volume"] is not None:
        md.daily_volume = kraken_data["daily_volume"]
    return md

# =========================
# Fetch all market data (synchronous)
# =========================
def fetch_bulk_market_data(pairs: List[str], token_map: Dict[str, str]) -> Dict[str, MarketData]:
    custom_logger.info("Fetching bulk CoinGecko market data...")
    cg_map = fetch_coingecko_data_bulk(list(token_map.values()))
    market_data_dict: Dict[str, MarketData] = {}

    for pair in pairs:
        token_id = token_map[pair]
        market_data_dict[pair] = fetch_market_data(pair, token_id, cg_map)

    return market_data_dict
