import pytest
from pathlib import Path
import pytz
from pydantic import ValidationError
from src.config import (
    LoggingConfig,
    EBoekhoudenConfig,
    DirectoryConfig,
    AppConfig,
    BrowserConfig,
    RetryConfig,
    DatabaseConfig
)

def test_logging_config_defaults():
    """Test LoggingConfig with default values."""
    config = LoggingConfig()
    assert config.level == "INFO"
    assert config.max_bytes == 10 * 1024 * 1024  # 10MB
    assert config.backup_count == 5
    assert config.log_dir == Path("logs")

def test_logging_config_custom_values():
    """Test LoggingConfig with custom values."""
    config = LoggingConfig(
        level="DEBUG",
        max_bytes=5 * 1024 * 1024,
        backup_count=3,
        log_dir=Path("custom_logs")
    )
    assert config.level == "DEBUG"
    assert config.max_bytes == 5 * 1024 * 1024
    assert config.backup_count == 3
    assert config.log_dir == Path("custom_logs")

def test_logging_config_validation():
    """Test LoggingConfig validation."""
    with pytest.raises(ValidationError):
        LoggingConfig(max_bytes=100)  # Too small
    
    with pytest.raises(ValidationError):
        LoggingConfig(backup_count=0)  # Must be >= 1

def test_eboekhouden_config():
    """Test EBoekhoudenConfig."""
    config = EBoekhoudenConfig(
        username="test_user",
        password="test_pass"
    )
    assert config.username == "test_user"
    assert config.password == "test_pass"
    assert config.base_url == "https://secure20.e-boekhouden.nl"
    assert "e-boekhouden.nl" in config.login_url

def test_directory_config_defaults():
    """Test DirectoryConfig with default values."""
    config = DirectoryConfig()
    assert config.output_dir == Path("output")
    assert config.temp_dir == Path("temp")
    assert config.screenshots_dir == Path("temp/screenshots")

def test_directory_config_custom():
    """Test DirectoryConfig with custom values."""
    config = DirectoryConfig(
        output_dir=Path("custom_output"),
        temp_dir=Path("custom_temp"),
        screenshots_dir=Path("custom_screenshots")
    )
    assert config.output_dir == Path("custom_output")
    assert config.temp_dir == Path("custom_temp")
    assert config.screenshots_dir == Path("custom_screenshots")

def test_app_config():
    """Test AppConfig initialization and defaults."""
    db_config = DatabaseConfig(
        server="test_server",
        database="test_db",
        username="test_user",
        password="test_pass"
    )
    
    eboekhouden_config = EBoekhoudenConfig(
        username="eb_user",
        password="eb_pass"
    )
    
    config = AppConfig(
        database=db_config,
        eboekhouden=eboekhouden_config
    )
    
    assert isinstance(config.browser, BrowserConfig)
    assert isinstance(config.retry, RetryConfig)
    assert config.database == db_config
    assert isinstance(config.logging, LoggingConfig)
    assert config.eboekhouden == eboekhouden_config
    assert isinstance(config.directories, DirectoryConfig)
    assert config.timezone == "Europe/Amsterdam"

def test_app_config_timezone():
    """Test AppConfig timezone property."""
    db_config = DatabaseConfig(
        server="test_server",
        database="test_db",
        username="test_user",
        password="test_pass"
    )
    
    eboekhouden_config = EBoekhoudenConfig(
        username="eb_user",
        password="eb_pass"
    )
    
    config = AppConfig(
        database=db_config,
        eboekhouden=eboekhouden_config,
        timezone="UTC"
    )
    
    assert isinstance(config.tz, pytz.BaseTzInfo)
    assert str(config.tz) == "UTC"

def test_app_config_invalid_timezone():
    """Test AppConfig with invalid timezone."""
    db_config = DatabaseConfig(
        server="test_server",
        database="test_db",
        username="test_user",
        password="test_pass"
    )
    
    eboekhouden_config = EBoekhoudenConfig(
        username="eb_user",
        password="eb_pass"
    )
    
    with pytest.raises(ValidationError):
        AppConfig(
            database=db_config,
            eboekhouden=eboekhouden_config,
            timezone="Invalid/Timezone"
        ) 