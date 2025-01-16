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

from src.container import Container
from src.eboekhouden import EBoekhoudenClient
from config import config

def setup_environment() -> None:
    """Initialize the application environment."""
    # Create required directories if they don't exist
    config.directories.output_dir.mkdir(exist_ok=True)
    config.directories.temp_dir.mkdir(exist_ok=True)
    config.directories.screenshots_dir.mkdir(exist_ok=True)

def cleanup_temp_files() -> None:
    """Move temporary HTML files to the temp directory."""
    temp_files = ["login_page.html", "page_content.html"]
    for file in temp_files:
        if os.path.exists(file):
            try:
                os.replace(file, config.directories.temp_dir / file)
            except OSError as e:
                logger.error(f"Error moving {file} to temp directory: {e}")

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

def main() -> int:
    """Main program entry point.
    
    Returns:
        0 for success, 1 for failure
    """
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize hours with e-boekhouden.nl')
    parser.add_argument('--year', type=int, help='Year to synchronize (defaults to current year)')
    args = parser.parse_args()
    
    # Set up logging
    logger = logging.getLogger(__name__)
    
    # Initialize container
    container = Container()
    
    try:
        # Initialize environment
        setup_environment()
        
        # Record start time in local timezone
        start_time = datetime.now(config.tz)
        logger.info(f"Starting application at {start_time.isoformat()}")
        
        # Use provided year or default to current year
        target_year = args.year if args.year else start_time.year
        logger.info(f"Target year for synchronization: {target_year}")
        
        # Step 1: Retrieve hour data from SQL Server database
        logger.info("Starting data retrieval from SQL Server database...")
        
        try:
            # Load the JSON schema for validation
            schema = container.load_schema()
        except Exception as e:
            logger.error(f"Failed to load JSON schema: {e}")
            return 1
            
        try:
            # Get events from database for target year
            events = container.get_events(target_year)
            
        except Exception as e:
            logger.error(f"Failed to retrieve events from database: {e}")
            return 1
        
        # Validate the events against schema
        try:
            if not container.validate_events(events, schema):
                logger.error("Events validation failed")
                return 1
                
            logger.info(f"Successfully retrieved and validated {len(events)} events")
            
            # Save events with timestamp
            output_path = container.save_events(events, start_time)
            logger.info(f"Saved retrieved hours to {output_path}")
            
            # Step 2: Log into e-boekhouden
            logger.info("Attempting to log into e-boekhouden...")
            client = container.get_eboekhouden_client()
            
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
            else:
                logger.error("Could not proceed with e-boekhouden operations due to login failure")
                return 1
                
        except Exception as e:
            logger.error(f"Failed to validate or save events: {e}")
            return 1
            
        # Record end time and duration
        end_time = datetime.now(config.tz)
        duration = end_time - start_time
        logger.info(f"Application completed successfully at {end_time.isoformat()}")
        logger.info(f"Total execution time: {duration}")
        
        return 0
            
    except Exception as e:
        logger.error(f"An unexpected error occurred in the main program: {e}", exc_info=True)
        return 1
    finally:
        container.cleanup()

if __name__ == "__main__":
    sys.exit(main()) 