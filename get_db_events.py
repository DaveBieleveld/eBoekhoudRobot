import json
import jsonschema
import logging
from src.database import get_db_connection
from src.logging_config import get_logger
from src.config import config

logger = get_logger("database")

def get_db_events(year: int) -> list:
    """Retrieve events from the database for a specific year.
    
    Args:
        year: The year to retrieve events for
    """
    # In development mode, force the year to test_year
    if config.development.enabled and year != config.development.test_year:
        logger.info(f"Development mode enabled - ignoring request for year {year}, using {config.development.test_year} instead")
        year = config.development.test_year

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # Read the SQL query from file
        with open('get_db_events.sql', 'r') as sql_file:
            sql_query = sql_file.read()

        # Execute query with year parameter
        params = (year,)
        cursor.execute(sql_query, params)
        
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

def load_json_schema(schema_path: str) -> dict:
    """Load a JSON schema from a file.
    
    Args:
        schema_path: Path to the schema file
        
    Returns:
        The loaded schema as a dictionary
    """
    try:
        with open(schema_path, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Failed to load schema from {schema_path}: {e}")
        raise

def validate_events(events: list, schema: dict) -> bool:
    """Validate events against a JSON schema.
    
    Args:
        events: List of events to validate
        schema: JSON schema to validate against
        
    Returns:
        True if validation succeeds, False otherwise
    """
    try:
        jsonschema.validate(instance=events, schema=schema)
        return True
    except jsonschema.exceptions.ValidationError as e:
        logger.error(f"Event validation failed: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error during validation: {e}")
        return False 