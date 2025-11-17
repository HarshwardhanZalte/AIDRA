import logging
import os
import sys

def get_logger(name: str) -> logging.Logger:
    """
    Configures and returns a standard logger.
    """
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if not logger.hasHandlers():
        handler = logging.StreamHandler(sys.stdout)
        handler.setLevel(log_level)
        
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)

    logger.propagate = False
    return logger

# Example of a global logger if needed, but per-module is better
# logger = get_logger(__name__)