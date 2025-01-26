from pydantic import BaseModel, Field, computed_field, model_validator
from typing import Dict, Any, Optional
import os
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BrowserConfig(BaseModel):
    """Browser-specific configuration."""
    headless: bool = Field(default=False)
    slow_mo: int = Field(default=25, ge=0)
    viewport_width: int = Field(default=1920, ge=800)
    viewport_height: int = Field(default=1080, ge=600)
    default_timeout: int = Field(default=5000, ge=1000)
    download_timeout: int = Field(default=30000, ge=5000)
    user_agent: str = Field(default="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")

class RetryConfig(BaseModel):
    """Retry mechanism configuration."""
    max_attempts: int = Field(default=60, ge=1)
    delay_ms: int = Field(default=100, ge=10)
    long_retry_max_attempts: int = Field(default=1000, ge=1)

class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    server: str
    database: str
    username: str
    password: str = ""
    trusted_connection: bool = False

    @computed_field
    def connection_string(self) -> str:
        """Get the database connection string."""
        if self.trusted_connection:
            return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};Trusted_Connection=yes;"
        return f"DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={self.server};DATABASE={self.database};UID={self.username};PWD={self.password};"

class LoggingConfig(BaseModel):
    """Logging configuration."""
    level: str = Field(default="INFO")
    max_bytes: int = Field(default=10 * 1024 * 1024, ge=1024)  # 10MB
    backup_count: int = Field(default=5, ge=1)
    log_dir: Path = Field(default=Path("logs"))

class EBoekhoudenConfig(BaseModel):
    """E-boekhouden specific configuration."""
    username: str = Field(default=...)
    password: str = Field(default=...)
    base_url: str = Field(default="https://secure20.e-boekhouden.nl")
    login_url: str = Field(default="https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A")
    table_columns: dict = Field(default={
        'date': 'td:nth-child(4)',
        'employee': 'td:nth-child(5)', 
        'project': 'td:nth-child(6)',
        'activity': 'td:nth-child(7)',
        'description': 'td:nth-child(8)',
        'hours': 'td:nth-child(9)',
        'kilometers': 'td:nth-child(10)'
    })

class DirectoryConfig(BaseModel):
    """Directory configuration."""
    output_dir: Path = Field(default=Path("output"))
    temp_dir: Path = Field(default=Path("temp"))
    screenshots_dir: Path = Field(default=Path("temp/screenshots"))

class DevelopmentConfig(BaseModel):
    """Development configuration."""
    enabled: bool = Field(default=False)
    test_year: int = Field(default=2023)

class AppConfig(BaseModel):
    """Main application configuration."""
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    database: DatabaseConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    eboekhouden: EBoekhoudenConfig
    directories: DirectoryConfig = Field(default_factory=DirectoryConfig)
    development: DevelopmentConfig = Field(default_factory=DevelopmentConfig)
    timezone: str = Field(default="Europe/Amsterdam")

    @property
    def tz(self) -> Any:
        """Get the timezone object."""
        return pytz.timezone(self.timezone)

def load_config() -> AppConfig:
    """Load and validate configuration from environment variables."""
    # Database configuration
    db_config = DatabaseConfig(
        server=os.getenv("DB_SERVER", ""),
        database=os.getenv("DB_NAME", ""),
        username=os.getenv("DB_USER", ""),
        password=os.getenv("DB_PASSWORD", ""),
        trusted_connection=os.getenv("DB_TRUSTED_CONNECTION", "").lower() == "yes"
    )

    # Browser configuration
    browser_config = BrowserConfig(
        headless=os.getenv("BROWSER_HEADLESS", "").lower() == "true",
        slow_mo=int(os.getenv("BROWSER_SLOW_MO", "25")),
        viewport_width=int(os.getenv("BROWSER_VIEWPORT_WIDTH", "1920")),
        viewport_height=int(os.getenv("BROWSER_VIEWPORT_HEIGHT", "1080")),
        default_timeout=int(os.getenv("BROWSER_DEFAULT_TIMEOUT", "5000")),
        download_timeout=int(os.getenv("BROWSER_DOWNLOAD_TIMEOUT", "30000")),
        user_agent=os.getenv("BROWSER_USER_AGENT", "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36")
    )

    # Retry configuration
    retry_config = RetryConfig(
        max_attempts=int(os.getenv("RETRY_MAX_ATTEMPTS", "60")),
        delay_ms=int(os.getenv("RETRY_DELAY_MS", "100")),
        long_retry_max_attempts=int(os.getenv("RETRY_LONG_MAX_ATTEMPTS", "1000"))
    )

    # E-boekhouden configuration
    eboekhouden_config = EBoekhoudenConfig(
        username=os.getenv("EBOEKHOUDEN_USERNAME", ""),
        password=os.getenv("EBOEKHOUDEN_PASSWORD", ""),
        base_url=os.getenv("EBOEKHOUDEN_BASE_URL", "https://secure20.e-boekhouden.nl"),
        login_url=os.getenv("EBOEKHOUDEN_LOGIN_URL", "https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A")
    )

    # Logging configuration
    logging_config = LoggingConfig(
        level=os.getenv("LOG_LEVEL", "INFO")
    )

    # Development configuration
    dev_config = DevelopmentConfig(
        enabled=os.getenv("DEV_MODE", "").lower() == "true",
        test_year=int(os.getenv("DEV_TEST_YEAR", "2023"))
    )

    # Create the main configuration
    return AppConfig(
        browser=browser_config,
        retry=retry_config,
        database=db_config,
        eboekhouden=eboekhouden_config,
        logging=logging_config,
        development=dev_config
    )

# Create a global config instance
config = load_config() 