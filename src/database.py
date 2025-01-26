from typing import List, Dict, Any
import pyodbc
import json
import logging
from src.config import config

logger = logging.getLogger(__name__)

def get_db_connection():
    """Get a connection to the database using configuration settings."""
    try:
        conn = pyodbc.connect(config.database.connection_string)
        logger.info("Successfully connected to database")
        return conn
    except pyodbc.Error as e:
        logger.error(f"Failed to connect to database: {e}")
        raise

class DatabaseClient:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_hours_data(self) -> List[Dict[Any, Any]]:
        """Retrieve hour data from SQL Server and return as JSON-compatible format."""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM your_hours_table 
                    WHERE YEAR(date_column) = YEAR(GETDATE())
                """)
                
                columns = [column[0] for column in cursor.description]
                results = []
                
                for row in cursor.fetchall():
                    results.append(dict(zip(columns, row)))
                
                logger.info(f"Retrieved {len(results)} hour records from database")
                return results
                
        except pyodbc.Error as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise 