from pydantic import BaseModel, Field
from typing import Dict, Any
import os
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class BrowserConfig(BaseModel):
    """Configuration settings for browser automation.
    
    Controls browser behavior including headless mode, animation timing,
    viewport dimensions, timeouts, and user agent string.

    Attributes:
        headless (bool): Whether to run browser in headless mode without GUI
        slow_mo (int): Delay in ms between actions to slow down automation
        viewport_width (int): Browser window width in pixels
        viewport_height (int): Browser window height in pixels
        default_timeout (int): Default timeout in ms for browser operations
        download_timeout (int): Specific timeout in ms for download operations
        user_agent (str): Browser user agent string to use for requests
    """
    headless: bool = False
    slow_mo: int = Field(default=25, ge=0)
    viewport_width: int = Field(default=1920, ge=800)
    viewport_height: int = Field(default=1080, ge=600)
    default_timeout: int = Field(default=5000, ge=1000)
    download_timeout: int = Field(default=30000, ge=5000)
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

class RetryConfig(BaseModel):
    """Configuration for retry mechanisms in case of failures.
    
    Defines retry behavior including number of attempts and delay between retries.

    Attributes:
        max_attempts (int): Maximum number of retry attempts for regular operations
        delay_ms (int): Delay in milliseconds between retry attempts
        long_retry_max_attempts (int): Maximum retries for long-running operations
    """
    max_attempts: int = Field(default=60, ge=1)
    delay_ms: int = Field(default=100, ge=10)
    long_retry_max_attempts: int = Field(default=1000, ge=1)

class DatabaseConfig(BaseModel):
    """Database connection configuration settings.
    
    Contains all necessary parameters to establish a database connection.

    Attributes:
        server (str): Database server hostname or IP
        database (str): Name of the database to connect to
        username (str): Database user username
        password (str): Database user password
        trusted_connection (bool): Whether to use Windows Authentication
    """
    server: str = Field(default=...)
    database: str = Field(default=...)
    username: str = Field(default=...)
    password: str = Field(default=...)
    trusted_connection: bool = False

class LoggingConfig(BaseModel):
    """Logging configuration settings.
    
    Controls logging behavior including log levels, rotation, and storage location.

    Attributes:
        level (str): Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        max_bytes (int): Maximum size of log file before rotation
        backup_count (int): Number of backup log files to keep
        log_dir (Path): Directory where log files will be stored
    """
    level: str = Field(default="INFO")
    max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)  # 10MB
    backup_count: int = Field(default=5, ge=1)
    log_dir: Path = Field(default=Path("logs"))

class EBoekhoudenConfig(BaseModel):
    """E-boekhouden.nl specific configuration.
    
    Contains authentication and URL configuration for e-Boekhouden.nl integration.

    Attributes:
        username (str): E-boekhouden.nl account username
        password (str): E-boekhouden.nl account password
        base_url (str): Base URL for API endpoints
        login_url (str): URL for authentication endpoint
    """
    username: str = Field(default=...)
    password: str = Field(default=...)
    base_url: str = "https://secure20.e-boekhouden.nl"
    login_url: str = "https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A"

class DirectoryConfig(BaseModel):
    """Directory structure configuration.
    
    Defines paths for various file operations including output and temporary files.

    Attributes:
        output_dir (Path): Directory for storing output files
        temp_dir (Path): Directory for temporary files
        screenshots_dir (Path): Directory for browser screenshots
    """
    output_dir: Path = Field(default=Path("output"))
    temp_dir: Path = Field(default=Path("temp"))
    screenshots_dir: Path = Field(default=Path("temp/screenshots"))

class AppConfig(BaseModel):
    """Main application configuration.
    
    Root configuration class that combines all sub-configurations into a single structure.
    Provides centralized access to all configuration settings.

    Attributes:
        browser (BrowserConfig): Browser automation settings
        retry (RetryConfig): Retry mechanism settings
        database (DatabaseConfig): Database connection settings
        logging (LoggingConfig): Logging configuration
        eboekhouden (EBoekhoudenConfig): E-boekhouden.nl specific settings
        directories (DirectoryConfig): File system directory settings
        timezone (str): Application timezone setting
    """
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    database: DatabaseConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    eboekhouden: EBoekhoudenConfig
    directories: DirectoryConfig = Field(default_factory=DirectoryConfig)
    timezone: str = Field(default="Europe/Amsterdam")

    @property
    def tz(self) -> Any:
        """Get the timezone object for the configured timezone.
        
        Returns:
            Any: A pytz timezone object for the configured timezone
        """
        return pytz.timezone(self.timezone)

def load_config() -> AppConfig:
    """Load and validate configuration from environment variables.
    
    Reads configuration values from environment variables and constructs
    a validated AppConfig instance. Environment variables are typically
    loaded from a .env file.
    
    Returns:
        AppConfig: A fully populated and validated configuration object
    """
    # Database configuration
    db_config = DatabaseConfig(
        server=os.getenv("DB_SERVER", ""),
        database=os.getenv("DB_NAME", ""),
        username=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        trusted_connection=os.getenv("DB_TRUSTED_CONNECTION", "").lower() == "yes"
    )

    # E-boekhouden configuration
    eboekhouden_config = EBoekhoudenConfig(
        username=os.getenv("EBOEKHOUDEN_USERNAME", ""),
        password=os.getenv("EBOEKHOUDEN_PASSWORD", "")
    )

    # Logging configuration
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO")
    )

    # Create the main configuration
    return AppConfig(
        database=db_config,
        eboekhouden=eboekhouden_config,
        logging=logging_config
    )

# Create a global config instance
config = load_config() 