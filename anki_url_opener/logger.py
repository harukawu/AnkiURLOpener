"""
Logging module for AnkiVoice add-on
"""
import os
import sys
import logging
from typing import Optional

from . import USER_FILES_PATH

# Configure logging
LOG_FILE = os.path.join(USER_FILES_PATH, "anki_voice.log")
LOG_FORMAT = "%(asctime)s - %(levelname)s - %(message)s"
LOG_LEVEL = logging.INFO  # Change to logging.DEBUG for more verbose output


def setup_logger() -> logging.Logger:
    """Set up and configure the logger
    
    Returns:
        The configured logger object
    """
    # Create logger
    logger = logging.getLogger("anki_voice")
    logger.setLevel(LOG_LEVEL)
    
    # Create file handler
    handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    handler.setFormatter(logging.Formatter(LOG_FORMAT))
    
    # Add handler to logger
    logger.addHandler(handler)
    
    return logger


# Global logger instance
logger = setup_logger()


def log_info(message: str) -> None:
    """Log an info message
    
    Args:
        message: The message to log
    """
    logger.info(message)


def log_error(message: str, exc: Optional[Exception] = None) -> None:
    """Log an error message
    
    Args:
        message: The error message to log
        exc: The exception that caused the error (optional)
    """
    if exc:
        logger.error(f"{message}: {str(exc)}")
    else:
        logger.error(message)


def log_debug(message: str) -> None:
    """Log a debug message
    
    Args:
        message: The debug message to log
    """
    logger.debug(message) 