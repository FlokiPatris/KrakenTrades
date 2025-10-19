from typing import Optional, Dict, List
import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed
from kraken_core import KrakenAPI, custom_logger, MarketData
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

COINGECKO_API = "https://api.coingecko.com/api/v3"
MAX_THREADS = 3  # limit concurrency to respect rate limits

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

def fetch_coin_dominance(token_id: str) -> Optional[float]:
    dominance_key = DOMINANCE_MAPPING.get(token_id.lower())
    if not dominance_key:
        return 0.0
    dominance_data = fetch_global_dominance()
    return float(dominance_data.get(dominance_key, 0))

# =========================
# Fetch CoinGecko bulk market data
# =========================
def fetch_coingecko_data_bulk(token_ids: List[str], vs_currency: str = "eur") -> Dict[str, MarketData]:
    md_map: Dict[str, MarketData] = {}
    try:
        ids = ",".join(token_ids)
        url = f"{COINGECKO_API}/coins/markets"
        resp = session.get(url, params={"vs_currency": vs_currency, "ids": ids}, timeout=10)
        resp.raise_for_status()
        data_list = resp.json()

        for data in data_list:
            md = MarketData()
            md.market_cap = float(data.get("market_cap", 0))
            md.daily_volume = float(data.get("total_volume", 0))
            md.price = float(data.get("current_price", 0))
            md.high_24h = float(data.get("high_24h", 0))
            md.low_24h = float(data.get("low_24h", 0))
            md.price_change_percentage_24h = float(data.get("price_change_percentage_24h", 0))
            md.market_cap_change_percentage_24h = float(data.get("market_cap_change_percentage_24h", 0))
            md.ath = float(data.get("ath", 0))
            md.ath_change_percentage = float(data.get("ath_change_percentage", 0))
            md.ath_date = data.get("ath_date")
            md.dominance = fetch_coin_dominance(data["id"])
            md_map[data["id"]] = md

    except Exception as e:
        custom_logger.warning(f"Failed bulk CoinGecko fetch: {e}")
    return md_map

# =========================
# Fetch 30-day historical chart
# =========================
def fetch_market_chart_30d(token_id: str, vs_currency: str = "eur") -> Optional[dict]:
    try:
        url = f"{COINGECKO_API}/coins/{token_id}/market_chart"
        resp = session.get(url, params={"vs_currency": vs_currency, "days": 30, "interval": "daily"}, timeout=10)
        resp.raise_for_status()
        prices = [p[1] for p in resp.json().get("prices", [])]
        if not prices:
            return None
        series = pd.Series(prices)
        return {
            "volatility_30d": float(series.pct_change().std()),
            "momentum_30d": float(series.iloc[-1] / series.mean() - 1),
        }
    except Exception as e:
        custom_logger.warning(f"Failed 30d market chart for {token_id}: {e}")
        return None

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
# Combine Kraken + CoinGecko + 30d data
# =========================
def fetch_market_data(pair: str, token_id: str, cg_map: Dict[str, MarketData]) -> MarketData:
    md = cg_map.get(token_id, MarketData())
    kraken_data = fetch_kraken_data(pair)
    if kraken_data["price"] is not None:
        md.price = kraken_data["price"]
    if kraken_data["daily_volume"] is not None:
        md.daily_volume = kraken_data["daily_volume"]
    chart = fetch_market_chart_30d(token_id)
    if chart:
        md.volatility_30d = chart["volatility_30d"]
        md.momentum_30d = chart["momentum_30d"]
    return md

# =========================
# Fetch all market data in bulk
# =========================
def fetch_bulk_market_data(pairs: List[str], token_map: Dict[str, str]) -> Dict[str, MarketData]:
    token_ids = list(token_map.values())
    custom_logger.info("Fetching bulk CoinGecko market data...")
    cg_map = fetch_coingecko_data_bulk(token_ids)

    market_data_dict: Dict[str, MarketData] = {}
    with ThreadPoolExecutor(max_workers=MAX_THREADS) as executor:
        future_map = {executor.submit(fetch_market_data, pair, token_map[pair], cg_map): pair for pair in pairs}
        for future in as_completed(future_map):
            pair = future_map[future]
            try:
                market_data_dict[pair] = future.result()
            except Exception as e:
                custom_logger.warning(f"Failed to fetch data for {pair}: {e}")

    return market_data_dict