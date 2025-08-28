import logging
from logging.handlers import RotatingFileHandler
import sys
from typing import Optional

import config


def configure_logging(
    *,
    level: int = logging.INFO,
    log_file: str = config.LOG_PATH,
    max_bytes: int = 2_000_000,
    backup_count: int = 3,
    fmt: str = config.LOG_FORMAT,
) -> None:
    """
    Configure root logging once. Safe to call multiple times (no duplicate handlers).
    """
    root = logging.getLogger()
    root.setLevel(level)

    # If already configured, don't add handlers again
    if getattr(root, "_talon_configured", False):
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
    Per-module logger. Use get_logger(__name__) in your modules.
    """
    return logging.getLogger(name if name else "talonbot")
