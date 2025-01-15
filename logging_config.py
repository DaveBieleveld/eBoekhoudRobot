import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

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
    db_logger.propagate = False  # Prevent propagation to root logger

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