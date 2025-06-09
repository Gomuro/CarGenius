# app/core/logger.py
import logging
from logging.handlers import RotatingFileHandler


# Create a rotating file handler:
# - Writes logs to "app.log"
# - When the log file reaches 5MB, it rolls over to a new file
# - Keeps up to 3 backup log files (app.log.1, app.log.2, etc.)
file_handler = RotatingFileHandler(
    "app.log",         # Log file name
    maxBytes=5 * 1024 * 1024,  # 5 MB
    backupCount=3,             # Keep 3 backup files
    encoding="utf-8"           # Encoding for the log file
)

# Define the log message format
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s")
file_handler.setFormatter(formatter)

# Create the main logger
logger = logging.getLogger("CarGenius")
logger.setLevel(logging.INFO)           # Set the minimum log level to INFO


# Prevent duplicate logs from being propagated to the root logger
logger.propagate = False

# Add both console (stdout) and rotating file handlers
logger.addHandler(logging.StreamHandler())  # Console handler for stdout
logger.addHandler(file_handler)             # Log to file with rotation
