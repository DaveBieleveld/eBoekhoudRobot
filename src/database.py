from typing import List, Dict, Any
import pyodbc  # We'll need to add this to conda.yaml
import json
import logging

logger = logging.getLogger(__name__)

class DatabaseClient:
    def __init__(self, connection_string: str):
        self.connection_string = connection_string
    
    def get_hours_data(self) -> List[Dict[Any, Any]]:
        """Retrieve hour data from SQL Server and return as JSON-compatible format."""
        try:
            with pyodbc.connect(self.connection_string) as conn:
                cursor = conn.cursor()
                # You'll need to provide the actual SQL query
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
                
        except Exception as e:
            logger.error(f"Database error: {str(e)}", exc_info=True)
            raise 