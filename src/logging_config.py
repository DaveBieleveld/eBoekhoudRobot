import logging
from logging.handlers import RotatingFileHandler
import os
from datetime import datetime
import json
from .config import config

# Create logs directory if it doesn't exist
os.makedirs(config.logging.log_dir, exist_ok=True)

# Configure component-specific log files
COMPONENTS = {
    'browser': {
        'file': 'browser.log',
        'level': getattr(logging, config.logging.level)
    },
    'network': {
        'file': 'network.log',
        'level': getattr(logging, config.logging.level)
    },
    'business': {
        'file': 'business.log',
        'level': getattr(logging, config.logging.level)
    }
}

# Common log format for all handlers
LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

def get_logger(component: str) -> logging.Logger:
    """Get a logger for a specific component with rotating file handler."""
    if component not in COMPONENTS:
        raise ValueError(f"Unknown component: {component}. Must be one of {list(COMPONENTS.keys())}")

    logger = logging.getLogger(f"eboekhouden.{component}")
    
    # Only add handlers if they haven't been added yet
    if not logger.handlers:
        logger.setLevel(COMPONENTS[component]['level'])
        
        # Create rotating file handler
        log_file = os.path.join(config.logging.log_dir, COMPONENTS[component]['file'])
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=config.logging.max_bytes,
            backupCount=config.logging.backup_count,
            encoding='utf-8'
        )
        
        # Create formatter and add it to the handler
        formatter = logging.Formatter(LOG_FORMAT, DATE_FORMAT)
        file_handler.setFormatter(formatter)
        
        # Add handler to logger
        logger.addHandler(file_handler)
        
        # Also add a stream handler for console output in development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    
    return logger

def log_dict(logger: logging.Logger, level: int, message: str, data: dict):
    """Log a dictionary as formatted JSON with a message."""
    logger.log(level, f"{message}\n{json.dumps(data, indent=2, ensure_ascii=False)}")

# Initialize all component loggers at module import
for component in COMPONENTS:
    get_logger(component) 