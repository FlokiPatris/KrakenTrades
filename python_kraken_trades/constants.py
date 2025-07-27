from pathlib import Path
import re

# === File Paths ===
KRAKEN_TRADES_PDF_PATH:   Path = Path(r"C:\Users\fkotr\Downloads\trades.pdf")
PARSED_TRADES_EXCEL_PATH: Path = Path("../kraken_trade_summary.xlsx")

# === API ===
KRAKEN_API_URL: str = "https://api.kraken.com/0/public/Ticker"
KRAKEN_TIMEOUT: int = 10

# === REGEX PATTERNS ===
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
TRADE_RE = re.compile(r"""
    ^(?P<date>\d{4}-\d{2}-\d{2})\s+
    (?P<uid>[A-Z0-9-]+)\s+
    (?P<pair>[A-Z0-9]+/[A-Z0-9]+)\s+
    (?P<type>Buy|Sell)\s+
    (?P<subtype>Limit|Market)\s+
    (?P<price>\d+\.\d+)\s+
    (?P<cost>\d+\.\d+)\s+
    (?P<volume>\d+\.\d+)\s+
    (?P<fee>\d+\.\d+)\s+
    (?P<margin>\d+\.\d+)$
""", re.VERBOSE)

# === excel Styling ===
HEADER_FILL_COLOR = {
    "positive": "C6EFCE",
    "negative": "FFC7CE"
}

CURRENCY_SUFFIX = "EUR"
