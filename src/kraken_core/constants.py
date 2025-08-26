# --------------------------------------------------------------------
# 🧰 Environment & Config
# --------------------------------------------------------------------
from __future__ import annotations
import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import FrozenSet
from dotenv import load_dotenv

from .enums import FolderType

load_dotenv()  # Load environment variables from .env file


# -------------------------
# Fail-fast helper for env vars
# -------------------------
def get_env_var(name: str, default: str | None = None, required: bool = False) -> str:
    """Fetch environment variable, fail fast if missing and required."""
    if name in os.environ:
        return os.environ[name]
    if required:
        raise EnvironmentError(f"Missing required environment variable: {name}")
    if default is not None:
        return default
    raise EnvironmentError(f"No value found for {name} and no default provided")


# === Repository Scanning Configuration ===
@dataclass(frozen=True)
class RepoScanConfig:
    """
    Configuration for scanning repository files.
    """

    SEPARATOR: str = "=" * 80

    # File extensions to include in scan
    INCLUDED_EXTENSIONS: FrozenSet[str] = frozenset(
        get_env_var(
            "SCAN_EXTENSIONS", ".py,.txt,.yml,.json,.md,Dockerfile,Makefile"
        ).split(",")
    )

    # Directories to skip during scanning
    SKIP_DIRS: FrozenSet[str] = frozenset(
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
    TREE_DEPTH: int = int(get_env_var("TREE_DEPTH", "10"))

    FALLBACK_CATEGORY: str = "other"
    CATEGORIES_TO_SCAN: FrozenSet[str] = frozenset(
        [".ci", ".github", "scripts", "src", "tests"]
    )


@dataclass(frozen=True)
class PathsConfig:
    """
    Centralized configuration for folders and files.
    - Folders: controlled via FolderType enum
    - Files: fixed paths, can be overridden via environment variables
    """

    # --- Files --- #
    KRAKEN_TRADES_PDF: Path = Path(
        get_env_var("KRAKEN_TRADES_PDF", "downloads/trades.pdf")
    )
    PARSED_TRADES_EXCEL: Path = Path(
        get_env_var("PARSED_TRADES_EXCEL", "uploads/kraken_trade_summary.xlsx")
    )

    # --- Folders --- #
    DOWNLOADS_DIR: Path = Path(get_env_var("DOWNLOADS_DIR", FolderType.DOWNLOADS.value))
    UPLOADS_DIR: Path = Path(get_env_var("UPLOADS_DIR", FolderType.UPLOADS.value))
    REPORTS_DIR: Path = Path(
        get_env_var("REPORTS_DIR", f"../{FolderType.REPORTS.value}")
    )

    # --- Repo root --- #
    REPO_ROOT: Path = Path(get_env_var("REPO_ROOT", ".")).resolve()


# === Database / RDS Configuration ===
@dataclass(frozen=True)
class PostgresConfig:
    host: str
    port: int
    dbname: str
    user: str
    password: str = field(repr=False)  # TODO important !! hide in repr for security

    @staticmethod
    def from_env() -> PostgresConfig:
        host = get_env_var("RDS_HOST", required=True)
        dbname = get_env_var("RDS_DB_NAME", required=True)
        user = get_env_var("RDS_USER", required=True)
        password = get_env_var("RDS_PASSWORD", required=True)
        port = int(get_env_var("RDS_PORT", default="5432"))

        return PostgresConfig(
            host=host, port=port, dbname=dbname, user=user, password=password
        )


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
    """Precompiled regex patterns for parsing trade data."""

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
    """Excel styling constants for header formatting."""

    HEADER_POSITIVE_FILL: str = "C6EFCE"  # Light green
    HEADER_NEGATIVE_FILL: str = "FFC7CE"  # Light red


# === Formatting Rules ===
@dataclass(frozen=True)
class FormatRules:
    """Formatting configuration for numeric precision."""

    DECIMAL_PLACES_10: int = 10
    DECIMAL_PLACES_2: int = 2
    DECIMAL_PLACES_8: int = 8
