import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Optional
from datetime import datetime

def setup_logger(
    name: str, 
    level: int = logging.INFO,
    log_file: Optional[str] = None,
    log_format: Optional[str] = None
) -> logging.Logger:
    """
    Setup and configure a logger instance.
    
    Args:
        name: Logger name (usually __name__)
        level: Logging level (default: INFO)
        log_file: Optional path to log file
        log_format: Optional custom log format
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    
    # Only configure logger if it hasn't been configured yet
    if not logger.handlers:
        logger.setLevel(level)
        
        # Default format
        if log_format is None:
            log_format = "[%(asctime)s] %(levelname)s [%(name)s] %(message)s"
        
        formatter = logging.Formatter(log_format)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # File handler (if specified)
        if log_file:
            try:
                # Create log directory if needed
                log_dir = os.path.dirname(log_file)
                if log_dir and not os.path.exists(log_dir):
                    os.makedirs(log_dir)
                    
                file_handler = logging.FileHandler(log_file)
                file_handler.setFormatter(formatter)
                logger.addHandler(file_handler)
            except Exception as e:
                logger.error(f"Failed to setup file logging: {str(e)}")
    
    return logger

def get_default_log_file() -> str:
    """Get default log file path"""
    log_dir = os.environ.get("LOG_DIR", "logs")
    
    # Create logs directory if it doesn't exist
    Path(log_dir).mkdir(parents=True, exist_ok=True)
    
    # Generate log filename with current date
    date_str = datetime.now().strftime("%Y-%m-%d")
    return os.path.join(log_dir, f"app_{date_str}.log")
