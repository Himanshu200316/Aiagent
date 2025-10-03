"""
Logging configuration
"""
import logging
import os
from datetime import datetime
from app.core.config import settings

def setup_logging():
    """Setup application logging"""
    
    # Create logs directory if it doesn't exist
    os.makedirs(settings.logs_dir, exist_ok=True)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'{settings.logs_dir}/app.log'),
            logging.StreamHandler()
        ]
    )
    
    # Create specific loggers
    logger = logging.getLogger('social_media_agent')
    logger.setLevel(logging.INFO)
    
    return logger

def get_logger(name: str):
    """Get logger instance"""
    return logging.getLogger(f'social_media_agent.{name}')