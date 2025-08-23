import os
import re
from dataclasses import dataclass
from pathlib import Path
from dotenv import load_dotenv

# Load .env if present
load_dotenv()


# === Repository Scanning Configuration ===
@dataclass(frozen=True)
class RepoScanConfig:
    """
    Configuration for scanning repository files.
    """

    SEPARATOR: str = "=" * 80

    # Root path of the repository (defaults to current working directory)
    REPO_ROOT: Path = Path(os.getenv("REPO_ROOT", ".")).resolve()

    # File extensions to include in scan
    INCLUDED_EXTENSIONS: frozenset = frozenset(
        os.getenv(
            "SCAN_EXTENSIONS", ".py,.txt,.yml,.json,.md,Dockerfile,Makefile"
        ).split(",")
    )

    # Directories to skip during scanning
    SKIP_DIRS: frozenset = frozenset(
        [
            ".git",
            ".hg",
            ".svn",
            "__pycache__",
            ".venv",
            "venv",
            "env",
            "build",
            "dist",
            ".idea",
            ".vscode",
            "tmp",
            "temp",
        ]
    )

    # Output file for extracted content
    OUTPUT_FILE: Path = Path(
        os.getenv("OUTPUT_FILE", "../reports/repository_extracted_contents.txt")
    )

    # Tree depth for printing repo structure
    TREE_DEPTH: int = int(os.getenv("TREE_DEPTH", 10))

    # Top-level folder categories for organizing scanned files
    TOP_LEVEL_CATEGORIES = [".ci", ".github", "scripts", "src", "tests"]


# === File Locations ===
@dataclass(frozen=True)
class FileLocations:
    """
    Centralized file path configuration.
    Reads from environment variables or falls back to defaults.
    """

    # Input / Output file names
    KRAKEN_TRADES_PDF: Path = Path(
        os.getenv("KRAKEN_TRADES_PDF", "downloads/trades.pdf")
    )
    PARSED_TRADES_EXCEL: Path = Path(
        os.getenv("PARSED_TRADES_EXCEL", "uploads/kraken_trade_summary.xlsx")
    )

    # Uploads directory for Docker runtime
    UPLOADS_DIR: Path = Path(os.getenv("UPLOADS_DIR", "uploads"))


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
        re.VERBOSE,
    )

    PAIR_CURRENCY = re.compile(r"/([A-Z]+)")
    PAIR_TOKEN = re.compile(r"^([A-Z0-9]+)/")


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

    DECIMAL_PLACES_10: int = 10
    DECIMAL_PLACES_2: int = 2
    DECIMAL_PLACES_8: int = 8
