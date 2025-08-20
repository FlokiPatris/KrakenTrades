from pydantic import BaseSettings


class KrakenExportConfig(BaseSettings):
    api_key: str
    api_secret: str
    start_ts: int
    end_ts: int
    output_pdf: str = "kraken_trades.pdf"

    class Config:
        env_file = ".env"
        env_prefix = "KRAKEN_"
