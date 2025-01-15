import logging
import json
import sys
from datetime import datetime
import pytz
from pathlib import Path
from typing import Dict, List, Any, Optional
import os
from dotenv import load_dotenv

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

def save_events(events: List[Dict[str, Any]], timestamp: datetime) -> Path:
    """Save events to a timestamped JSON file.
    
    Args:
        events: List of event dictionaries to save
        timestamp: Timestamp to use in filename
    
    Returns:
        Path to the saved file
    """
    filename = f"hours_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
    output_path = OUTPUT_DIR / filename
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(events, f, indent=2, ensure_ascii=False)
    
    return output_path

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
        
        # Step 1: Retrieve hour data from SQL Server database
        logger.info("Starting data retrieval from SQL Server database...")
        
        try:
            # Load the JSON schema for validation
            schema = load_json_schema('schemas/events.schema.json')
        except Exception as e:
            logger.error(f"Failed to load JSON schema: {e}")
            return 1
            
        try:
            # Get events from database
            events = get_events()
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