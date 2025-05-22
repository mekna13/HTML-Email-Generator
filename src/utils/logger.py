# app/utils/logger.py
import logging
import sys

def setup_logger(name="tamu_newsletter"):
    """
    Sets up and returns a logger with file and console handlers
    
    Args:
        name: Name of the logger
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Only set up handlers if they haven't been set up yet
    if not logger.handlers:
        logger.setLevel(logging.INFO)
        
        # Create handlers
        file_handler = logging.FileHandler("app_debug.log")
        console_handler = logging.StreamHandler(sys.stdout)
        
        # Create formatter and add it to the handlers
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
    
    return logger

# Create a default app logger instance
# DO NOT import anything else here that might cause circular imports
app_logger = setup_logger()