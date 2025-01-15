import json
import pyodbc
import logging
import os
import time
from jsonschema import validate
from datetime import datetime
from typing import Dict, Any
from dotenv import load_dotenv
from logging_config import setup_logging

# Load environment variables
load_dotenv()

# Configure logging
root_logger, db_logger = setup_logging()
logger = logging.getLogger(__name__)

def load_json_schema(schema_path: str) -> Dict[str, Any]:
    """Load and parse the JSON schema file."""
    try:
        with open(schema_path, 'r') as schema_file:
            return json.load(schema_file)
    except Exception as e:
        logger.error(f"Failed to load schema file: {e}")
        raise

def get_db_connection(max_retries: int = 3, retry_delay: int = 5) -> pyodbc.Connection:
    """Create and return a database connection with retry logic.
    
    Args:
        max_retries: Maximum number of connection attempts
        retry_delay: Delay in seconds between retries
    """
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            conn_str = (
                "DRIVER={SQL Server};"
                f"SERVER={os.getenv('DB_SERVER')};"
                f"DATABASE={os.getenv('DB_NAME')};"
                "Connection Timeout=30;"  # 30 seconds timeout
            )

            if os.getenv('DB_TRUSTED_CONNECTION', 'yes').lower() == 'yes':
                conn_str += "Trusted_Connection=yes;"
            else:
                conn_str += f"UID={os.getenv('DB_USER')};"
                conn_str += f"PWD={os.getenv('DB_PASSWORD')};"

            conn = pyodbc.connect(conn_str)
            db_logger.info("Successfully established database connection")
            return conn

        except Exception as e:
            last_error = e
            retry_count += 1
            if retry_count < max_retries:
                db_logger.warning(f"Connection attempt {retry_count} failed: {e}. Retrying in {retry_delay} seconds...")
                time.sleep(retry_delay)
            else:
                db_logger.error(f"Failed to connect to database after {max_retries} attempts: {e}")
                raise last_error

def get_events() -> list:
    """Retrieve events from the database using the SQL query."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Read the SQL query from file
        with open('get_events.sql', 'r') as sql_file:
            sql_query = sql_file.read()

        cursor.execute(sql_query)
        
        # Fetch all rows to handle potential multiple JSON fragments
        rows = cursor.fetchall()
        if not rows:
            return []

        # Combine all JSON fragments
        json_fragments = [row[0] for row in rows if row[0] is not None]
        if not json_fragments:
            return []

        result_json = ''.join(json_fragments)
        
        # Debug: Log the JSON string
        logger.debug(f"Raw JSON length: {len(result_json)}")
        logger.debug(f"JSON preview (first 200 chars): {result_json[:200]}")
        logger.debug(f"JSON end (last 200 chars): {result_json[-200:] if len(result_json) > 200 else result_json}")
        
        try:
            # Parse the JSON string into a Python object
            events = json.loads(result_json)
            logger.info(f"Successfully parsed {len(events)} events")
            return events
        except json.JSONDecodeError as je:
            # Get more context around the error
            error_pos = je.pos
            start_pos = max(0, error_pos - 100)
            end_pos = min(len(result_json), error_pos + 100)
            context = result_json[start_pos:end_pos]
            logger.error(f"JSON parsing error at position {error_pos}")
            logger.error(f"Error context: ...{context}...")
            logger.error(f"Error message: {str(je)}")
            # Log the full JSON string for debugging
            logger.debug(f"Full JSON string: {result_json}")
            raise

    except Exception as e:
        logger.error(f"Failed to retrieve events: {e}")
        raise

def validate_events(events: list, schema: Dict[str, Any]) -> bool:
    """Validate the events against the JSON schema."""
    try:
        validate(instance=events, schema=schema)
        return True
    except Exception as e:
        logger.error(f"JSON validation failed: {e}")
        raise

def test_connection():
    """Test database connection and query."""
    try:
        conn = get_db_connection()
        logger.info("Successfully connected to database")
        
        cursor = conn.cursor()
        cursor.execute("SELECT @@VERSION")
        version = cursor.fetchone()[0]
        logger.info(f"SQL Server version: {version}")
        
        cursor.close()
        conn.close()
        return True
    except Exception as e:
        logger.error(f"Connection test failed: {e}")
        return False

def main():
    try:
        # Test connection first
        if not test_connection():
            logger.error("Database connection test failed. Exiting.")
            return
            
        # Load the JSON schema
        schema = load_json_schema('schemas/events.schema.json')
        
        # Get events from database
        logger.info("Retrieving events from database...")
        events = get_events()
        
        # Validate events against schema
        logger.info("Validating events against schema...")
        if validate_events(events, schema):
            logger.info(f"Successfully validated {len(events)} events")
            
            # You can process the events further here
            for event in events:
                logger.info(f"Event: {event['subject']} - {event['start_date']}")
        
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        raise

if __name__ == "__main__":
    main() 