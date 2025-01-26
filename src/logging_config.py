import os
import logging
from logging.handlers import RotatingFileHandler
from typing import Dict, Any, Tuple
import json
from src.config import config

def setup_logging() -> Tuple[logging.Logger, logging.Logger]:
    """Set up logging configuration."""
    # Create required directories if they don't exist
    os.makedirs('logs', exist_ok=True)
    os.makedirs(config.directories.output_dir, exist_ok=True)
    os.makedirs(config.directories.temp_dir, exist_ok=True)
    os.makedirs(config.directories.screenshots_dir, exist_ok=True)

    # Common format for all loggers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger first
    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
    # Clear any existing handlers
    root_logger.handlers.clear()
    root_logger.addHandler(console_handler)

    # Main application logger
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(formatter)
    app_logger = logging.getLogger('app')
    app_logger.handlers.clear()
    app_logger.addHandler(app_handler)
    app_logger.propagate = False  # Prevent propagation to root logger

    # Database operations logger
    db_handler = RotatingFileHandler(
        'logs/database.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    db_handler.setFormatter(formatter)
    db_logger = logging.getLogger('database')
    db_logger.handlers.clear()
    db_logger.addHandler(db_handler)
    db_logger.propagate = False

    # Error logger (separate file for errors)
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)
    error_logger = logging.getLogger('error')
    error_logger.handlers.clear()
    error_logger.addHandler(error_handler)
    error_logger.propagate = False  # Prevent propagation to root logger

    return root_logger, db_logger

def get_logger(component: str) -> logging.Logger:
    """Get a logger for a specific component."""
    return logging.getLogger(component)

def log_dict(logger: logging.Logger, level: int, message: str, data: Dict[str, Any]) -> None:
    """Log a dictionary with proper formatting."""
    logger.log(level, f"{message}: {json.dumps(data, indent=2)}") 