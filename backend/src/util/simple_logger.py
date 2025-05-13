"""
Simple Logger Module
A lightweight, configurable logging utility for the AI search engine
"""
import os
import sys
import logging
from datetime import datetime
from typing import Optional

# Constants
DEFAULT_LOG_LEVEL = logging.INFO
DEFAULT_LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
DEFAULT_DATE_FORMAT = "%Y-%m-%d %H:%M:%S"

# Environment variable for log level
LOG_LEVEL_ENV_VAR = "NEXUS_LOG_LEVEL"
LOG_FILE_ENV_VAR = "NEXUS_LOG_FILE"

# Map string log levels to logging constants
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
    "critical": logging.CRITICAL
}

def get_log_level() -> int:
    """Get log level from environment variable or use default"""
    log_level_str = os.getenv(LOG_LEVEL_ENV_VAR, "info").lower()
    return LOG_LEVELS.get(log_level_str, DEFAULT_LOG_LEVEL)

def get_log_file() -> Optional[str]:
    """Get log file path from environment variable"""
    return os.getenv(LOG_FILE_ENV_VAR)

def setup_logger(name: str) -> logging.Logger:
    """
    Set up and configure a logger instance
    
    Args:
        name: Name of the logger (typically __name__)
        
    Returns:
        Configured logging.Logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure if it hasn't been configured already
    if not logger.handlers:
        # Set level
        logger.setLevel(get_log_level())
        
        # Create formatters
        formatter = logging.Formatter(DEFAULT_LOG_FORMAT, DEFAULT_DATE_FORMAT)
        
        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # Add file handler if log file is specified
        log_file = get_log_file()
        if log_file:
            try:
                # Create directory if it doesn't exist
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir, exist_ok=True)
                
                # Add timestamp to log filename to avoid overwrites
                timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
                filename, ext = os.path.splitext(log_file)
                log_file_with_timestamp = f"{filename}_{timestamp}{ext}"
                
                file_handler = logging.FileHandler(log_file_with_timestamp)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                # Don't fail if we can't set up file logging, just log to console
                console_handler.setLevel(logging.WARNING)
                logger.warning(f"Failed to set up log file: {str(e)}")
    
    return logger 