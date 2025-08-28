# =============================================================================
# 📝 Logger Manager
# =============================================================================
import logging
import sys
from typing import Optional, Final


# =============================================================================
# 🐍 LoggerManager Class
# =============================================================================
class LoggerManager:
    """
    Singleton logger manager for Kraken trades.
    Centralizes logging configuration and supports future AWS CloudWatch integration.
    """

    _instance: Optional["LoggerManager"] = None
    logger: logging.Logger

    DEFAULT_NAME: Final[str] = "trades"
    LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

    def __new__(cls, name: str = DEFAULT_NAME) -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configure_logger(name)
        return cls._instance

    def _configure_logger(self, name: str) -> None:
        """
        Configure the logger with a StreamHandler and formatter.
        Prevents duplicate handlers and allows future AWS CloudWatch integration.
        """
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # prevent double logging

        if not self.logger.handlers:
            # Standard output handler
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(fmt=self.LOG_FORMAT, datefmt=self.DATE_FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            # Placeholder for future CloudWatch integration
            # self._add_cloudwatch_handler()

    # Example for future AWS CloudWatch integration
    # def _add_cloudwatch_handler(self) -> None:
    #     import watchtower
    #     cw_handler = watchtower.CloudWatchLogHandler(log_group="kraken-trades")
    #     self.logger.addHandler(cw_handler)


# =============================================================================
# ✅ Global Singleton Logger
# =============================================================================
custom_logger: Final[logging.Logger] = LoggerManager().logger
