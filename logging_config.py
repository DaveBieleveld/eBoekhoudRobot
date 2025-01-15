import os
import logging
from logging.handlers import RotatingFileHandler

def setup_logging():
    # Create logs directory if it doesn't exist
    if not os.path.exists('logs'):
        os.makedirs('logs')

    # Common format for all loggers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Main application logger
    app_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    app_handler.setFormatter(formatter)

    # Database operations logger
    db_handler = RotatingFileHandler(
        'logs/database.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    db_handler.setFormatter(formatter)

    # Error logger (separate file for errors)
    error_handler = RotatingFileHandler(
        'logs/error.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    error_handler.setFormatter(formatter)
    error_handler.setLevel(logging.ERROR)

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(os.getenv('LOG_LEVEL', 'INFO'))
    root_logger.addHandler(console_handler)
    root_logger.addHandler(app_handler)
    root_logger.addHandler(error_handler)

    # Configure database logger
    db_logger = logging.getLogger('database')
    db_logger.addHandler(db_handler)

    return root_logger, db_logger 