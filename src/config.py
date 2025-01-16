from pydantic import BaseModel, Field
from typing import Dict, Any
import os
from pathlib import Path
import pytz
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class BrowserConfig(BaseModel):
    """Browser-specific configuration."""
    headless: bool = False
    slow_mo: int = Field(default=25, ge=0)
    viewport_width: int = Field(default=1920, ge=800)
    viewport_height: int = Field(default=1080, ge=600)
    default_timeout: int = Field(default=5000, ge=1000)
    download_timeout: int = Field(default=30000, ge=5000)
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"

class RetryConfig(BaseModel):
    """Retry mechanism configuration."""
    max_attempts: int = Field(default=60, ge=1)
    delay_ms: int = Field(default=100, ge=10)
    long_retry_max_attempts: int = Field(default=1000, ge=1)

class DatabaseConfig(BaseModel):
    """Database connection configuration."""
    server: str = Field(default=...)
    database: str = Field(default=...)
    username: str = Field(default=...)
    password: str = Field(default=...)
    trusted_connection: bool = False

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
    base_url: str = "https://secure20.e-boekhouden.nl"
    login_url: str = "https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A"

class DirectoryConfig(BaseModel):
    """Directory configuration."""
    output_dir: Path = Field(default=Path("output"))
    temp_dir: Path = Field(default=Path("temp"))
    screenshots_dir: Path = Field(default=Path("temp/screenshots"))

class AppConfig(BaseModel):
    """Main application configuration."""
    browser: BrowserConfig = Field(default_factory=BrowserConfig)
    retry: RetryConfig = Field(default_factory=RetryConfig)
    database: DatabaseConfig
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    eboekhouden: EBoekhoudenConfig
    directories: DirectoryConfig = Field(default_factory=DirectoryConfig)
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