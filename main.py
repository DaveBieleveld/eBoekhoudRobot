"""Main entry point for e-boekhouden synchronization."""

import os
import json
import logging
import argparse
from datetime import datetime
from src.config import config
from src.eboekhouden import EBoekhoudenClient
from src.container import Container
from src.logging_config import setup_logging

def cleanup_temp_files():
    """Clean up temporary files."""
    try:
        # Clean up temp directory
        for file in os.listdir(config.directories.temp_dir):
            file_path = os.path.join(config.directories.temp_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logging.error(f"Error deleting {file_path}: {str(e)}")
                
        # Clean up screenshots directory
        for file in os.listdir(config.directories.screenshots_dir):
            file_path = os.path.join(config.directories.screenshots_dir, file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                logging.error(f"Error deleting {file_path}: {str(e)}")
                
    except Exception as e:
        logging.error(f"Error during cleanup: {str(e)}")

def main():
    """Main entry point."""
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Synchronize events with e-boekhouden')
    parser.add_argument('--year', type=int, help='Year to synchronize')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')
    args = parser.parse_args()
    
    # Set up logging
    root_logger, db_logger = setup_logging()
    
    # Create output directories
    os.makedirs(config.directories.output_dir, exist_ok=True)
    os.makedirs(config.directories.temp_dir, exist_ok=True)
    os.makedirs(config.directories.screenshots_dir, exist_ok=True)
    
    # Clean up temp files from previous runs
    cleanup_temp_files()
    
    # Log start
    start_time = datetime.now()
    logging.info(f"Application started at {start_time.isoformat()}")
    
    # Get target year
    target_year = args.year
    if config.development.enabled:
        target_year = config.development.test_year
        logging.info(f"Development mode enabled, forcing year to {target_year}")
    
    try:
        # Initialize container
        container = Container()
        
        # Get events from database
        logging.info(f"Getting events from database for year {target_year}")
        events = container.get_db_events(target_year)
        logging.info(f"Found {len(events)} events in database")
        
        # Save database events
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        db_events_path = os.path.join(config.directories.output_dir, f"database_events_{timestamp}.json")
        with open(db_events_path, 'w') as f:
            json.dump(events, f, indent=2)
        logging.info(f"Saved database events to {db_events_path}")
        
        # Initialize e-boekhouden client
        client = EBoekhoudenClient(
            username=config.eboekhouden.username,
            password=config.eboekhouden.password
        )
        
        # Log in to e-boekhouden
        logging.info("Logging in to e-boekhouden")
        if not client.perform_login():
            raise Exception("Login failed")
        
        # Download current events from e-boekhouden
        logging.info(f"Downloading hours for year {target_year}")
        xls_path, eboekhouden_events = client.download_hours_xls(target_year)
        logging.info(f"Found {len(eboekhouden_events)} events in e-boekhouden")
        
        # Synchronize events
        stats = container.synchronize_events(events, eboekhouden_events, target_year, dry_run=args.dry_run)
        
        # Log results
        if args.dry_run:
            logging.info("DRY-RUN complete - no changes were made to e-boekhouden")
        else:
            logging.info("Synchronization complete")
            
        logging.info(f"Stats: {json.dumps(stats, indent=2)}")
        
    except Exception as e:
        logging.error(f"Error during synchronization: {str(e)}")
        raise
        
    finally:
        # Clean up resources
        if 'client' in locals():
            client.cleanup()
        cleanup_temp_files()
        
        # Log end
        end_time = datetime.now()
        duration = end_time - start_time
        logging.info(f"Application finished at {end_time.isoformat()}")
        logging.info(f"Total duration: {duration}")

if __name__ == '__main__':
    main() 