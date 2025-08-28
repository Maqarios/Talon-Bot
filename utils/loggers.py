import logging
import os

import config

log_path = config.LOG_PATH

# Create logger
LOGGER = logging.getLogger("talonbot")
LOGGER.setLevel(logging.DEBUG)

# Create formatter
formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")

# Console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
console_handler.setFormatter(formatter)

# File handler
file_handler = logging.FileHandler(log_path, mode="a")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(formatter)

# Attach handlers only once (avoid duplicates on reloads)
if not LOGGER.handlers:
    LOGGER.addHandler(console_handler)
    LOGGER.addHandler(file_handler)
