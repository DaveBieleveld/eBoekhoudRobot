# eBoekhoudRobot

An automated RPA (Robotic Process Automation) solution for synchronizing hour data between a local SQL Server database and e-boekhouden.nl.

## Project Objectives

1. Retrieve hour data from a local SQL Server database in JSON format
2. Log in to the e-boekhouden website
3. Fetch existing hour data for a financial year (default: current year)
4. Compare and synchronize data:
   - Add new hours from database to e-boekhouden
   - Update modified hours in e-boekhouden
   - Delete non-invoiced hours from e-boekhouden if they're not in the database
5. Preserve invoiced hours in e-boekhouden (no modifications/deletions)
6. Comprehensive logging of all actions and errors
7. Support for local execution and scheduling (cron/Windows Task Scheduler)

## Configuration Structure

The application uses a hierarchical configuration system based on Pydantic models:

1. **Browser Configuration**
   - Controls Playwright browser behavior
   - Configures viewport, timeouts, and user agent
   - Supports headless mode for automated runs

2. **Retry Configuration**
   - Defines retry behavior for operations
   - Configures delays between attempts
   - Separate settings for long-running operations

3. **Database Configuration**
   - SQL Server connection settings
   - Support for Windows Authentication
   - Configurable through environment variables

4. **Logging Configuration**
   - Log level control (DEBUG to CRITICAL)
   - File rotation settings
   - Structured logging with timestamps

5. **E-boekhouden Configuration**
   - Authentication credentials
   - API endpoints
   - Session management

6. **Directory Configuration**
   - Output file locations
   - Temporary file management
   - Screenshot storage for debugging

## Prerequisites

- Python 3.8+
- SQL Server database
- e-boekhouden.nl account
- Required Python packages:
  - playwright
  - pydantic
  - pytz
  - python-dotenv
  - pandas (for XLS processing)

## Installation

1. Clone this repository
2. Create and activate a Python virtual environment
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```
5. Create a `.env` file with required credentials:
   ```env
   DB_SERVER=your_server
   DB_NAME=your_database
   DB_USER=your_username
   DB_PASSWORD=your_password
   DB_TRUSTED_CONNECTION=yes/no
   
   EBOEKHOUDEN_USERNAME=your_username
   EBOEKHOUDEN_PASSWORD=your_password
   
   LOG_LEVEL=INFO
   ```

## Usage

Basic usage:
```bash
python main.py
```

Specify a target year:
```bash
python main.py --year 2024
```

## Project Structure

```
eBoekhoudRobot/
├── src/                    # Core source code
│   ├── eboekhouden.py     # E-boekhouden automation
│   └── logging_config.py   # Logging setup
├── schemas/               # JSON schemas
│   └── events.schema.json # Event validation schema
├── docs/                 # Documentation
├── output/               # Generated files
├── temp/                 # Temporary files
├── logs/                 # Log files
├── config.py            # Configuration system
├── main.py             # Entry point
└── requirements.txt    # Dependencies
```

## Error Handling

The application implements comprehensive error handling:
- Detailed logging of all operations
- Screenshot capture on failures
- HTML content preservation for debugging
- Retry mechanisms for transient failures
- Graceful cleanup of resources

## Development

For development:
1. Fork and clone the repository
2. Create a feature branch
3. Install development dependencies
4. Run tests before committing
5. Submit pull requests with clear descriptions

## License

[MIT License](LICENSE)

## Support

For support and questions:
1. Check the documentation in `docs/`
2. Review logs in `logs/`
3. Create an issue in the repository
4. Include relevant logs and screenshots 