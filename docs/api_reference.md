# eBoekhoudRobot API Reference

## EBoekhoudenClient

The main class for interacting with e-boekhouden.nl web interface.

### Constructor

```python
def __init__(self, config: Optional[AppConfig] = None)
```

Creates a new EBoekhoudenClient instance.

**Parameters:**
- `config`: Optional[AppConfig] - Application configuration. If not provided, loads from environment.

**Raises:**
- `ConfigurationError`: If required configuration is missing
- `BrowserError`: If browser initialization fails

### Authentication

```python
def login(self, username: str, password: str) -> bool
```

Authenticates with e-boekhouden.nl.

**Parameters:**
- `username`: str - E-boekhouden username
- `password`: str - E-boekhouden password

**Returns:**
- `bool`: True if login successful, False otherwise

**Raises:**
- `AuthenticationError`: If login fails
- `TimeoutError`: If page load times out
- `NetworkError`: If connection fails

### Hour Registration

```python
def fetch_hours(self, year: int) -> Dict[str, Any]
```

Retrieves hour registrations for specified year.

**Parameters:**
- `year`: int - Target year for hour registrations

**Returns:**
- `Dict[str, Any]`: Dictionary containing:
  - `year`: int - Year of data
  - `data`: List[Dict] - Hour registrations
  - `timestamp`: str - Fetch timestamp

**Raises:**
- `DataRetrievalError`: If data fetch fails
- `ValidationError`: If data validation fails

```python
def download_hours_xls(self, year: int) -> tuple[str, list[dict]]
```

Downloads hour registrations as XLS file.

**Parameters:**
- `year`: int - Target year for download

**Returns:**
- `tuple[str, list[dict]]`: 
  - Path to downloaded file
  - Parsed data as list of dictionaries

**Raises:**
- `DownloadError`: If file download fails
- `ParseError`: If XLS parsing fails

### Data Processing

```python
def _parse_hours_xls(self, xls_path: str) -> list[dict]
```

Parses downloaded XLS file into structured data.

**Parameters:**
- `xls_path`: str - Path to XLS file

**Returns:**
- `list[dict]`: List of hour registration records

**Raises:**
- `ParseError`: If parsing fails
- `ValidationError`: If data validation fails

### Error Handling

```python
def _save_page_content(self, prefix: str) -> None
```

Saves current page content for debugging.

**Parameters:**
- `prefix`: str - Prefix for saved files

**Returns:**
- None

### Resource Management

```python
def close(self) -> None
```

Closes browser and cleans up resources.

**Returns:**
- None

## Container

Dependency injection container managing component lifecycle.

### Constructor

```python
def __init__(self)
```

Creates new Container instance.

### Client Management

```python
def get_eboekhouden_client(self) -> Optional[EBoekhoudenClient]
```

Gets or creates EBoekhoudenClient instance.

**Returns:**
- `Optional[EBoekhoudenClient]`: Client instance or None if creation fails

### Data Management

```python
def get_events(self, year: int) -> list[dict]
```

Retrieves events for specified year.

**Parameters:**
- `year`: int - Target year

**Returns:**
- `list[dict]`: List of events

```python
def save_events(self, events: list[dict], timestamp: datetime) -> Path
```

Saves events to file.

**Parameters:**
- `events`: list[dict] - Events to save
- `timestamp`: datetime - Timestamp for filename

**Returns:**
- `Path`: Path to saved file

### Schema Management

```python
def load_schema(self) -> dict
```

Loads JSON validation schema.

**Returns:**
- `dict`: Schema definition

```python
def validate_events(self, events: list[dict], schema: dict) -> bool
```

Validates events against schema.

**Parameters:**
- `events`: list[dict] - Events to validate
- `schema`: dict - Validation schema

**Returns:**
- `bool`: True if valid, False otherwise

### Resource Management

```python
def cleanup(self) -> None
```

Cleans up resources.

## Configuration

### LoggingConfig

Configuration for logging system.

**Attributes:**
- `level`: str - Logging level (default: "INFO")
- `max_bytes`: int - Max log file size (default: 10MB)
- `backup_count`: int - Number of backup files (default: 5)
- `log_dir`: Path - Log directory (default: "logs")

### EBoekhoudenConfig

Configuration for e-boekhouden integration.

**Attributes:**
- `username`: str - Account username
- `password`: str - Account password
- `base_url`: str - API base URL
- `login_url`: str - Login endpoint

### DirectoryConfig

Configuration for file system operations.

**Attributes:**
- `output_dir`: Path - Output directory
- `temp_dir`: Path - Temporary files
- `screenshots_dir`: Path - Screenshot storage

### AppConfig

Main application configuration.

**Attributes:**
- `browser`: BrowserConfig - Browser settings
- `retry`: RetryConfig - Retry settings
- `database`: DatabaseConfig - Database connection
- `logging`: LoggingConfig - Logging settings
- `eboekhouden`: EBoekhoudenConfig - Integration settings
- `directories`: DirectoryConfig - File system settings
- `timezone`: str - Application timezone

## Logging

### get_logger

```python
def get_logger(component: str) -> logging.Logger
```

Gets component-specific logger.

**Parameters:**
- `component`: str - Component name

**Returns:**
- `logging.Logger`: Configured logger

**Raises:**
- `ValueError`: If component unknown 