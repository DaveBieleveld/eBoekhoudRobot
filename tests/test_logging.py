import pytest
import logging
import os
import shutil
from pathlib import Path
from src.logging_config import get_logger, COMPONENTS, LOG_FORMAT, DATE_FORMAT
from src.config import config

@pytest.fixture
def temp_log_dir(tmp_path):
    """Create a temporary log directory."""
    log_dir = tmp_path / "logs"
    log_dir.mkdir()
    # Temporarily override config log directory
    original_log_dir = config.logging.log_dir
    config.logging.log_dir = log_dir
    yield log_dir
    # Restore original log directory
    config.logging.log_dir = original_log_dir
    # Clean up
    if log_dir.exists():
        shutil.rmtree(log_dir)

def test_get_logger_unknown_component():
    """Test get_logger with unknown component."""
    with pytest.raises(ValueError) as exc_info:
        get_logger("unknown_component")
    assert "Unknown component" in str(exc_info.value)
    assert str(list(COMPONENTS.keys())) in str(exc_info.value)

def test_get_logger_creates_handlers(temp_log_dir):
    """Test that get_logger creates appropriate handlers."""
    logger = get_logger("browser")
    
    # Should have two handlers: file and console
    assert len(logger.handlers) == 2
    
    # Verify handlers
    file_handler = next((h for h in logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)), None)
    console_handler = next((h for h in logger.handlers if isinstance(h, logging.StreamHandler) and not isinstance(h, logging.handlers.RotatingFileHandler)), None)
    
    assert file_handler is not None
    assert console_handler is not None
    
    # Verify file handler configuration
    assert file_handler.maxBytes == config.logging.max_bytes
    assert file_handler.backupCount == config.logging.backup_count
    assert isinstance(file_handler.formatter, logging.Formatter)
    assert file_handler.formatter._fmt == LOG_FORMAT
    assert file_handler.formatter.datefmt == DATE_FORMAT

def test_get_logger_file_creation(temp_log_dir):
    """Test that log files are created in the correct location."""
    logger = get_logger("browser")
    logger.info("Test message")
    
    log_file = temp_log_dir / "browser.log"
    assert log_file.exists()
    
    # Verify log content
    content = log_file.read_text()
    assert "Test message" in content
    assert "INFO" in content
    assert "eboekhouden.browser" in content

def test_get_logger_rotation(temp_log_dir):
    """Test log file rotation."""
    logger = get_logger("browser")
    log_file = temp_log_dir / "browser.log"
    
    # Write enough data to trigger rotation
    large_msg = "x" * (config.logging.max_bytes + 1000)
    logger.info(large_msg)
    
    # Check that rotation occurred
    assert log_file.exists()
    assert (temp_log_dir / "browser.log.1").exists()

def test_get_logger_multiple_calls():
    """Test that multiple calls to get_logger return the same logger instance."""
    logger1 = get_logger("browser")
    logger2 = get_logger("browser")
    assert logger1 is logger2
    
    # Handlers should not be duplicated
    assert len(logger1.handlers) == 2

def test_get_logger_levels(temp_log_dir):
    """Test logger level configuration."""
    # Test each component
    for component, settings in COMPONENTS.items():
        logger = get_logger(component)
        assert logger.level == getattr(logging, settings['level'])
        
        # Verify log file path
        log_file = temp_log_dir / settings['file']
        logger.info(f"Test message for {component}")
        assert log_file.exists()

def test_log_message_format(temp_log_dir):
    """Test that log messages are properly formatted."""
    logger = get_logger("browser")
    test_message = "Test log message"
    logger.info(test_message)
    
    log_file = temp_log_dir / "browser.log"
    content = log_file.read_text()
    
    # Check format components
    assert test_message in content
    assert "INFO" in content
    assert "eboekhouden.browser" in content
    # Check timestamp format (YYYY-MM-DD HH:MM:SS)
    assert any(line.split(" - ")[0].strip().match(r'\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}') 
              for line in content.splitlines()) 