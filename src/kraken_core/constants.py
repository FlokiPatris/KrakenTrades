import os
import re
from dataclasses import dataclass
from pathlib import Path

from .enums import FolderType


# === Repository Scanning Configuration ===
@dataclass(frozen=True)
class RepoScanConfig:
    """
    Configuration for scanning repository files.
    """

    SEPARATOR: str = "=" * 80

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

    # Tree depth for printing repo structure
    TREE_DEPTH: int = int(os.getenv("TREE_DEPTH", 10))

    FALLBACK_CATEGORY: str = "other"
    CATEGORIES_TO_SCAN: frozenset = frozenset(
        [".ci", ".github", "scripts", "src", "tests"]
    )


@dataclass(frozen=True)
class PathsConfig:
    """
    Centralized configuration for folders and files.
    - Folders: controlled via FolderType enum
    - Files: fixed paths, can be overridden via environment variables
    """

    # --- Files ---
    KRAKEN_TRADES_PDF: Path = Path(
        os.getenv("KRAKEN_TRADES_PDF", "downloads/trades.pdf")
    )
    PARSED_TRADES_EXCEL: Path = Path(
        os.getenv("PARSED_TRADES_EXCEL", "uploads/kraken_trade_summary.xlsx")
    )

    # --- Folders # --
    DOWNLOADS_DIR: Path = Path(
        os.getenv("DOWNLOADS_DIR", f"{FolderType.DOWNLOADS.value}")
    )
    UPLOADS_DIR: Path = Path(os.getenv("UPLOADS_DIR", f"{FolderType.UPLOADS.value}"))
    REPORTS_DIR: Path = Path(os.getenv("REPORTS_DIR", f"../{FolderType.REPORTS.value}"))

    # --- Repo root ---
    REPO_ROOT: Path = Path(os.getenv("REPO_ROOT", ".")).resolve()


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
