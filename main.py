import logging
import json
import sys
from datetime import datetime
import pytz
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv
import time
import argparse

from get_events import get_events, load_json_schema, validate_events
from logging_config import setup_logging
from src.eboekhouden import EBoekhoudenClient

# Constants
OUTPUT_DIR = Path("output")
TEMP_DIR = Path("temp")
TIMEZONE = pytz.timezone("Europe/Amsterdam")

def setup_environment() -> None:
    """Initialize the application environment."""
    # Create required directories if they don't exist
    OUTPUT_DIR.mkdir(exist_ok=True)
    TEMP_DIR.mkdir(exist_ok=True)

def cleanup_temp_files() -> None:
    """Move temporary HTML files to the temp directory."""
    temp_files = ["login_page.html", "page_content.html"]
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.replace(file, TEMP_DIR / file)
            except OSError as e:
                logger.error(f"Error moving {file} to temp directory: {e}")

def save_events(events: List[Dict[str, Any]], timestamp: datetime, source: str = "database") -> Path:
    """Save events to a timestamped JSON file.
    
    Args:
        events: List of event dictionaries to save
        timestamp: Timestamp to use in filename
        source: Source of the events ("database" or "e-boekhouden")
    
    Returns:
        Path to the saved file
    """
    prefix = "database" if source == "database" else "e-boekhouden"
    filename = f"{prefix}_events_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    return output_path

def download_hours_xls(client: EBoekhoudenClient, year: int) -> tuple[Optional[Path], Optional[list[dict]]]:
    """Download hours overview as XLS file for the specified year and convert to JSON.
    
    Args:
        client: Authenticated EBoekhoudenClient instance
        year: Year to download hours for
        
    Returns:
        Tuple of (Path to downloaded file if successful, List of event dictionaries if successful)
        Returns (None, None) if either operation fails
    """
    logger = logging.getLogger(__name__)
    logger.info(f"Downloading hours XLS for year {year}")
    
    try:
        xls_path, events = client.download_hours_xls(year)
        if xls_path and events:
            logger.info(f"Successfully downloaded hours XLS to: {xls_path}")
            logger.info(f"Successfully parsed {len(events)} events from XLS")
            return Path(xls_path), events
        else:
            logger.error("Failed to download or parse hours XLS")
            return None, None
    except Exception as e:
        logger.error(f"Error downloading/parsing hours XLS: {e}")
        return None, None

def login_to_eboekhouden() -> Optional[EBoekhoudenClient]:
    """Log into e-boekhouden.nl using credentials from environment variables.
    
    Returns:
        EBoekhoudenClient if login successful, None otherwise
    """
    username = os.getenv("EBOEKHOUDEN_USERNAME")
    password = os.getenv("EBOEKHOUDEN_PASSWORD")
    
    if not all([username, password]):
        logger.error("Missing required environment variables for e-boekhouden login")
        return None
    
    client = EBoekhoudenClient()
    try:
        success = client.login(username, password)
        if not success:
            logger.error("Failed to login to e-boekhouden")
            return None
        return client
    except Exception as e:
        logger.error(f"Error during e-boekhouden login: {e}")
        return None
    
def main() -> int:
    """Main program entry point.
    
    Returns:
        0 for success, 1 for failure
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize hours with e-boekhouden.nl')
    parser.add_argument('--year', type=int, help='Year to synchronize (defaults to current year)')
    args = parser.parse_args()
    
    # Load environment variables
    load_dotenv()
    
    # Set up logging
    root_logger, db_logger = setup_logging()
    logger = logging.getLogger(__name__)
    
    try:
        # Initialize environment
        setup_environment()
        
        # Record start time in local timezone
        start_time = datetime.now(TIMEZONE)
        logger.info(f"Starting application at {start_time.isoformat()}")
        
        # Use provided year or default to current year
        target_year = args.year if args.year else start_time.year
        logger.info(f"Target year for synchronization: {target_year}")
        
        # Step 1: Retrieve hour data from SQL Server database
        logger.info("Starting data retrieval from SQL Server database...")
        
        try:
            # Load the JSON schema for validation
            schema = load_json_schema('schemas/events.schema.json')
        except Exception as e:
            logger.error(f"Failed to load JSON schema: {e}")
            return 1
            
        try:
            # Get events from database for target year
            events = get_events(target_year)
            
        except Exception as e:
            logger.error(f"Failed to retrieve events from database: {e}")
            return 1
        
        # Validate the events against schema
        try:
            if validate_events(events, schema):
                logger.info(f"Successfully retrieved and validated {len(events)} events")
                
                # Save events with timestamp
                output_path = save_events(events, start_time)
                logger.info(f"Saved retrieved hours to {output_path}")
                
                # Step 2: Log into e-boekhouden
                logger.info("Attempting to log into e-boekhouden...")
                client = login_to_eboekhouden()
                
                if client:
                    try:
                        # Download hours XLS for target year
                        logger.info(f"Attempting to download hours for year {target_year}")
                        xls_path, events = download_hours_xls(client, target_year)
                        if xls_path:
                            logger.info(f"Hours XLS downloaded to: {xls_path}")
                            # Wait a moment to ensure file is properly saved
                            time.sleep(2)
                        else:
                            logger.warning("Could not download hours XLS")
                        
                        # TODO: Implement e-boekhouden operations here
                        # - Fetch existing hour data
                        # - Compare with database events
                        # - Add/update/delete hours as needed
                        pass
                    finally:
                        cleanup_temp_files()
                        client.close()
                else:
                    logger.error("Could not proceed with e-boekhouden operations due to login failure")
                    return 1
                
        except Exception as e:
            logger.error(f"Failed to validate or save events: {e}")
            return 1
            
        # Record end time and duration
        end_time = datetime.now(TIMEZONE)
        duration = end_time - start_time
        logger.info(f"Application completed successfully at {end_time.isoformat()}")
        logger.info(f"Total execution time: {duration}")
        
        return 0
            
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main program: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main()) 