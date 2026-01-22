"""Simple logging for SentimentDelta - can be imported from anywhere."""

import logging
import sys
from pathlib import Path
from datetime import datetime
import os

from config.config import ApiConfig


def get_logger(name=None, level=ApiConfig.LOG_LEVEL, log_file=None):
    """
    Get a simple logger that can be used anywhere in the project.
    
    Args:
        name: Logger name (if None, uses the calling module name)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional log file path (if None, uses default logs/app.log)
    
    Returns:
        Configured logger instance
    """
    if name is None:
        name = __name__
        
    logger = logging.getLogger(name)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    
    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s \n',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (always enabled)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler
    if log_file is None:
        # Create default log file in logs directory
        log_file = "logs/app.log"
    
    log_path = Path(log_file)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger