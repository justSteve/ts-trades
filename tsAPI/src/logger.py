"""Logger configuration for the TradeStation API client."""
import logging
import sys
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance configured with standard settings.

    Args:
        name: Optional name for the logger. Defaults to 'ts' if None.

    Returns:
        A configured logging.Logger instance
    """
    logger = logging.getLogger(name or 'ts')

    # Only add handlers if none exist to prevent duplicate handlers
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            fmt='%(asctime)s.%(msecs)03d %(levelname)s %(name)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set default level to INFO
        logger.setLevel(logging.INFO)

    return logger
