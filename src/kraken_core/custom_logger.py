# =============================================================================
# 📝 Auto Module Logger
# =============================================================================
import logging
import sys
import inspect
from typing import Final

# Log message format and timestamp format
LOG_FORMAT: Final[str] = "%(asctime)s | %(levelname)-5s | %(name)-18s | %(message)s"
DATE_FORMAT: Final[str] = "%Y-%m-%d %H:%M:%S"

# Singleton dict to store already created loggers per module
# Ensures that each module reuses its logger instead of creating multiple handlers
_loggers = {}


class AutoLogger:
    """
    Logger proxy that automatically provides a logger named after the calling module.

    Features:
    - Automatically detects the module that called the logger.
    - If the module name contains a dot (e.g., 'file_management.trade_report_data'),
      only the last part after the dot is used (e.g., 'trade_report_data').
    - Reuses loggers via a singleton dictionary to prevent duplicate handlers.
    - Supports all standard logging methods like `.info()`, `.error()`, `.warning()`, etc.

    Example usage:
        custom_logger.info("Hello world")
        # If called from file_management.trade_report_data:
        # Output: 2025-09-09 16:14:02 | INFO  | trade_report_data | Hello world
    """

    def __getattr__(self, attr):
        """
        Intercepts attribute access (like .info, .error) and returns the corresponding
        method from the dynamically created logger for the calling module.

        Returns:
            logging method (e.g., Logger.info, Logger.error, Logger.warning)
            bound to the logger of the calling module.

        How it works:
        1. `inspect.stack()[1]` gets the frame of the caller (who called the logger).
        2. `inspect.getmodule(frame[0])` retrieves the module object of the caller.
        3. `module.__name__` is the full module path (e.g., 'file_management.trade_report_data').
        4. If a dot exists, only the last part is kept for readability.
        5. Checks `_loggers` to reuse an existing logger or create a new one.
        6. Returns the requested logging method (e.g., .info, .error) from that logger.
        """
        # Get the caller's frame
        frame = inspect.stack()[1]
        module = inspect.getmodule(frame[0])
        name = module.__name__ if module else "root"

        # Keep only the last part after a dot, e.g., 'trade_report_data'
        if "." in name:
            name = name.split(".")[-1]

        # Create and configure the logger if it doesn't exist
        if name not in _loggers:
            logger = logging.getLogger(name)
            logger.setLevel(logging.INFO)
            logger.propagate = False  # Prevent double logging if root logger exists

            if not logger.handlers:
                # Standard output stream handler
                handler = logging.StreamHandler(sys.stdout)
                formatter = logging.Formatter(fmt=LOG_FORMAT, datefmt=DATE_FORMAT)
                handler.setFormatter(formatter)
                logger.addHandler(handler)

            # Save the logger in the singleton dictionary
            _loggers[name] = logger

        # Return the requested method (info, error, warning, etc.) from the logger
        return getattr(_loggers[name], attr)


# Global dynamic logger instance
# Import this in any module and it automatically uses the calling module's name
custom_logger = AutoLogger()
