# kraken_core/config.py
from pydantic import BaseSettings

class Settings(BaseSettings):
    KRAKEN_API_KEY: str
    KRAKEN_API_SECRET: str
    BASE_URL: str = "https://api.kraken.com/0/public/Ticker"

    class Config:
        env_file = ".env"

settings = Settings()
