"""
Logging utility for the End of Life Checker.
"""

import logging
import sys
from typing import Optional

# Configure logger
logger = logging.getLogger("eol_checker")
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setLevel(logging.INFO)

# Create formatter
formatter = logging.Formatter('%(message)s')
console_handler.setFormatter(formatter)

# Add handler to logger
logger.addHandler(console_handler)

# Flag to track if logger has been configured
_logger_configured = False


def configure_logger(verbose: bool = False, log_file: Optional[str] = None):
    """Configure the logger.
    
    Args:
        verbose: If True, set log level to DEBUG
        log_file: Path to log file (optional)
    """
    global _logger_configured
    
    if _logger_configured:
        return
    
    # Set log level based on verbose flag
    if verbose:
        logger.setLevel(logging.DEBUG)
        console_handler.setLevel(logging.DEBUG)
    
    # Add file handler if log file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG if verbose else logging.INFO)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    _logger_configured = True


def debug(message: str):
    """Log a debug message.
    
    Args:
        message: Message to log
    """
    logger.debug(message)


def info(message: str):
    """Log an info message.
    
    Args:
        message: Message to log
    """
    logger.info(message)


def warning(message: str):
    """Log a warning message.
    
    Args:
        message: Message to log
    """
    logger.warning(message)


def error(message: str):
    """Log an error message.
    
    Args:
        message: Message to log
    """
    logger.error(message)


def critical(message: str):
    """Log a critical message.
    
    Args:
        message: Message to log
    """
    logger.critical(message)
