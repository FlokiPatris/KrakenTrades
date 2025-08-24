# kraken_core/logger_manager.py
import logging
import sys
from typing import Optional


class LoggerManager:
    """
    Singleton logger manager for kraken trades.
    Centralizes logging configuration and allows easy AWS CloudWatch integration later.
    """

    _instance: Optional["LoggerManager"] = None
    logger: logging.Logger

    def __new__(cls, name: str = "trades") -> "LoggerManager":
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._configure_logger(name)
        return cls._instance

    def _configure_logger(self, name: str) -> None:
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        self.logger.propagate = False  # Prevent double logging

        if not self.logger.handlers:
            # Stdout handler
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(
                fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)

            # Placeholder: add AWS CloudWatch handler here in the future
            # self._add_cloudwatch_handler()

    # Example for future AWS CloudWatch integration
    # def _add_cloudwatch_handler(self):
    #     import watchtower
    #     cw_handler = watchtower.CloudWatchLogHandler(log_group="kraken-trades")
    #     self.logger.addHandler(cw_handler)


# ✅ Global singleton logger
custom_logger = LoggerManager().logger
