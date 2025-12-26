# Logger configuration
"""Logging setup for Racing Dashboard Configurator."""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler
from typing import Optional


# Log directory
LOG_DIR = Path.home() / ".racing_dashboard" / "logs"
LOG_FILE = LOG_DIR / "configurator.log"
ERROR_LOG_FILE = LOG_DIR / "errors.log"

# Log format
LOG_FORMAT = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
DATE_FORMAT = "%Y-%m-%d %H:%M:%S"


def setup_logging(
    level: int = logging.INFO,
    console: bool = True,
    file: bool = True
) -> None:
    """
    Setup application logging.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        console: Enable console output
        file: Enable file output
    """
    # Create log directory
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Clear existing handlers
    root_logger.handlers.clear()

    # Formatter
    formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)

    # Console handler
    if console:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        root_logger.addHandler(console_handler)

    # File handler (rotating, 10MB max, 5 backups)
    if file:
        file_handler = RotatingFileHandler(
            LOG_FILE,
            maxBytes=10 * 1024 * 1024,  # 10 MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

        # Error file handler
        error_handler = RotatingFileHandler(
            ERROR_LOG_FILE,
            maxBytes=5 * 1024 * 1024,  # 5 MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(formatter)
        root_logger.addHandler(error_handler)

    logging.info("Logging initialized")


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Get a logger instance.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "racing_dashboard")
