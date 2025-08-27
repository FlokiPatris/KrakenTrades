import os
import sys
import pandas as pd
import psycopg2
from psycopg2.extras import execute_values
from kraken_core import custom_logger  # adjust if your import path differs

from dotenv import load_dotenv

load_dotenv()  # Load environment variables from .env file

DB_CONFIG = {
    "host": os.environ.get("RDS_HOST", ""),
    "port": int(os.environ.get("RDS_PORT", 5432)),
    "database": os.environ.get("RDS_DB_NAME", ""),
    "user": os.environ.get("RDS_USER", ""),
    "password": os.environ.get("RDS_PASSWORD", ""),
}


def validate_env_vars() -> None:
    """Fail fast if any required DB env var is missing."""
    missing_vars = [k for k, v in DB_CONFIG.items() if not v]
    if missing_vars:
        custom_logger.error(
            "❌ Missing required DB environment variables: %s", missing_vars
        )
        sys.exit(1)


validate_env_vars()

TABLES = {
    "portfolio_summary": """
        CREATE TABLE IF NOT EXISTS portfolio_summary (
            id SERIAL PRIMARY KEY,
            metric TEXT NOT NULL,
            eur_value NUMERIC
        )
    """,
    "asset_roi": """
        CREATE TABLE IF NOT EXISTS asset_roi (
            id SERIAL PRIMARY KEY,
            token TEXT NOT NULL,
            pair TEXT,
            total_cost NUMERIC,
            realized_sells NUMERIC,
            unrealized_value NUMERIC,
            total_value NUMERIC,
            roi NUMERIC,
            potential_roi NUMERIC
        )
    """,
}

EXCEL_FILE = "uploads/kraken_trade_summary.xlsx"


def clean_numeric(series: pd.Series) -> pd.Series:
    """Remove symbols/emojis and convert to float."""
    return (
        series.astype(str)
        .str.replace(r"[^\d.-]", "", regex=True)
        .replace("", "0")
        .astype(float)
    )


# Load Portfolio
portfolio_df = pd.read_excel(EXCEL_FILE, sheet_name="Portfolio")
portfolio_df["EUR Value"] = clean_numeric(portfolio_df["EUR Value"])

# Load Asset ROI
asset_roi_df = pd.read_excel(EXCEL_FILE, sheet_name="Asset ROI")
numeric_cols = [
    "Total Cost (€)",
    "Realized Sells (€)",
    "Unrealized Value (€)",
    "Total Value (€)",
    "ROI (%)",
    "Potential ROI (%)",
]

for col in numeric_cols:
    asset_roi_df[col] = clean_numeric(asset_roi_df[col])

try:
    with psycopg2.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            custom_logger.info("✅ DB connection established")

            # Create tables if not exists
            for name, ddl in TABLES.items():
                cur.execute(ddl)
                custom_logger.info(f"✅ Ensured table exists: {name}")

            # Insert Portfolio
            portfolio_records = portfolio_df[["Metric", "EUR Value"]].values.tolist()
            insert_portfolio = """
                INSERT INTO portfolio_summary (metric, eur_value) VALUES %s
            """
            execute_values(cur, insert_portfolio, portfolio_records)
            custom_logger.info("✅ Portfolio data inserted")

            # Insert Asset ROI
            asset_records = asset_roi_df[
                [
                    "token",
                    "pair",
                    "Total Cost (€)",
                    "Realized Sells (€)",
                    "Unrealized Value (€)",
                    "Total Value (€)",
                    "ROI (%)",
                    "Potential ROI (%)",
                ]
            ].values.tolist()
            insert_asset_roi = """
                INSERT INTO asset_roi (token, pair, total_cost, realized_sells,
                                       unrealized_value, total_value, roi, potential_roi)
                VALUES %s
            """
            execute_values(cur, insert_asset_roi, asset_records)
            custom_logger.info("✅ Asset ROI data inserted")

except Exception as e:
    custom_logger.error("❌ DB operation failed: %s", e)
    sys.exit(1)

custom_logger.info("🎉 All data inserted successfully!")
