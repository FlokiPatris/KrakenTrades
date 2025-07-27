from dataclasses import dataclass
from pathlib import Path
import re

# === File Locations ===
@dataclass(frozen=True)
class FileLocations:
    """
    Centralized file path configuration.
    Replace hardcoded paths with environment variables or config loaders in production.
    """
    KRAKEN_TRADES_PDF: Path = Path(r"C:\Users\fkotr\Downloads\trades.pdf")  # TODO: move to .env
    PARSED_TRADES_EXCEL: Path = Path("../../kraken_trade_summary.xlsx")        # TODO: move to .env


# === API Configuration ===
@dataclass(frozen=True)
class KrakenAPI:
    """
    Kraken API configuration.
    Suitable for use in CI/CD and Docker environments.
    """
    URL: str = "https://api.kraken.com/0/public/Ticker"
    TIMEOUT: int = 10  # seconds


# === Regex Patterns ===
class TradeRegex:
    """
    Precompiled regex patterns for parsing trade data.
    """
    DATE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

    TRADE = re.compile(
        r"""^
        (?P<date>\d{4}-\d{2}-\d{2})\s+
        (?P<uid>[A-Z0-9-]+)\s+
        (?P<pair>[A-Z0-9]+/[A-Z0-9]+)\s+
        (?P<type>Buy|Sell)\s+
        (?P<subtype>Limit|Market)\s+
        (?P<price>\d+\.\d+)\s+
        (?P<cost>\d+\.\d+)\s+
        (?P<volume>\d+\.\d+)\s+
        (?P<fee>\d+\.\d+)\s+
        (?P<margin>\d+\.\d+)$
        """,
        re.VERBOSE
    )
    #TODO why no compile here?
    PAIR_CURRENCY = r"/([A-Z]+)"
    PAIR_TOKEN = r"^([A-Z0-9]+)/"


# === Excel Styling ===
@dataclass(frozen=True)
class ExcelStyling:
    """
    Excel styling constants for header formatting.
    These are used with openpyxl's PatternFill and Font.
    """
    HEADER_POSITIVE_FILL: str = "C6EFCE"  # Light green
    HEADER_NEGATIVE_FILL: str = "FFC7CE"  # Light red


# === Formatting Rules ===
@dataclass(frozen=True)
class FormatRules:
    """
    Formatting configuration for numeric precision.
    """
    ROUNDING_DECIMAL_PLACES: int = 10