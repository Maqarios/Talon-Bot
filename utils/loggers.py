import logging
from logging.handlers import RotatingFileHandler
import sys
from typing import Optional

import config

# Disable overly verbose logging from external libraries
logging.getLogger("discord").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("watchdog").setLevel(logging.WARNING)


def configure_logging(
    *,
    level: int = logging.INFO,
    log_file: str = config.LOG_PATH,
    max_bytes: int = 5_000_000,
    backup_count: int = 5,
    fmt: str = config.LOG_FORMAT,
) -> None:
    """
    Configures logging for the application with both console and rotating file handlers.
    Parameters:
        level (int, optional): Logging level for the root logger and console handler. Defaults to logging.INFO.
        log_file (str, optional): Path to the log file. Defaults to config.LOG_PATH.
        max_bytes (int, optional): Maximum size in bytes for a log file before rotation. Defaults to 5,000,000.
        backup_count (int, optional): Number of backup log files to keep. Defaults to 5.
        fmt (str, optional): Log message format. Defaults to config.LOG_FORMAT.
    Returns:
        None
    Notes:
        - Prevents duplicate handler configuration by checking a custom attribute.
        - Console handler logs at the specified level; file handler logs at DEBUG level.
        - Uses RotatingFileHandler for file logging with rotation based on file size.
    """
    root = logging.getLogger()
    root.setLevel(level)

    # If already configured, don't add handlers again
    if getattr(root, "_logger_configured", False):
        return

    formatter = logging.Formatter(fmt)

    # Console
    console = logging.StreamHandler(stream=sys.stdout)
    console.setLevel(level)
    console.setFormatter(formatter)

    # Rotating file
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding="utf-8"
    )
    file_handler.setLevel(logging.DEBUG)  # keep DEBUG in file
    file_handler.setFormatter(formatter)

    root.addHandler(console)
    root.addHandler(file_handler)

    # mark as configured to prevent duplication
    root._talon_configured = True  # type: ignore[attr-defined]


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Returns a logger instance for the specified module or a default logger.

    Args:
        name (Optional[str]): The name of the logger, typically the module's __name__. If None, uses "Talon Bot" as the default logger name.

    Returns:
        logging.Logger: A logger object for the specified module or the default logger.

    Usage:
        Use get_logger(__name__) in your modules to obtain a per-module logger.
    """
    return logging.getLogger(name if name else "Talon Bot")
