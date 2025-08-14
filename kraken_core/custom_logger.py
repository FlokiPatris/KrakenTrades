import logging
import sys


def _create_custom_logger(name: str = "trades") -> logging.Logger:
    """
    Internal function to configure the logger once.
    """
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    return logger


# ✅ Global logger instance — import and use directly
custom_logger: logging.Logger = _create_custom_logger()
