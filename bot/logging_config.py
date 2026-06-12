"""
trading_bot/bot/logging_config.py

Configures structured logging for the trading bot.
Logs are written to both the console (INFO level) and a rotating log file (DEBUG level).
"""

import logging
import os
from logging.handlers import RotatingFileHandler

# ── Constants ──────────────────────────────────────────────────────────────────
LOG_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "logs")
LOG_FILE = os.path.join(LOG_DIR, "trading.log")

# Max 5 MB per log file, keep 3 backups
MAX_BYTES = 5 * 1024 * 1024
BACKUP_COUNT = 3

# Log format includes timestamp, logger name, level, and message
LOG_FORMAT = "%(asctime)s | %(name)-20s | %(levelname)-8s | %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(log_level: str = "DEBUG") -> logging.Logger:
    """
    Set up and return the root logger for the trading bot.

    Args:
        log_level: Minimum log level for the file handler (default: DEBUG).

    Returns:
        Configured root logger instance.
    """
    # Ensure the logs directory exists
    os.makedirs(LOG_DIR, exist_ok=True)

    logger = logging.getLogger("trading_bot")
    logger.setLevel(logging.DEBUG)  # capture everything; handlers filter below

    # Prevent adding duplicate handlers if called more than once
    if logger.handlers:
        return logger

    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)

    # ── File handler (DEBUG and above → rotating log file) ────────────────────
    file_handler = RotatingFileHandler(
        LOG_FILE,
        maxBytes=MAX_BYTES,
        backupCount=BACKUP_COUNT,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    # ── Console handler (INFO and above → stdout) ─────────────────────────────
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    logger.debug("Logging initialised. Log file: %s", LOG_FILE)
    return logger
