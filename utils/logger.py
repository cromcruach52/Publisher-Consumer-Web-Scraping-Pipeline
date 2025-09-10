import logging
import sys
import os
from datetime import datetime

def setup_logger(name: str = "pipeline", level: str = None) -> logging.Logger:
    """Setup a simple logger"""
    if level is None:
        level = os.getenv("LOG_LEVEL", "INFO")
        
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Avoid duplicate handlers
    if logger.handlers:
        return logger
    
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    return logger

# Global logger instance
logger = setup_logger()
