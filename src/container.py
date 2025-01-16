from typing import Optional, Dict, Any
from pathlib import Path
import logging
import json
from datetime import datetime

from src.eboekhouden import EBoekhoudenClient
from src.logging_config import get_logger
from config import config
from get_events import get_events, load_json_schema, validate_events

class Container:
    """Service container for dependency injection."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client: Optional[EBoekhoudenClient] = None
        
    def get_eboekhouden_client(self) -> Optional[EBoekhoudenClient]:
        """Get or create an authenticated EBoekhoudenClient instance."""
        if not self._client:
            self._client = EBoekhoudenClient()
            try:
                success = self._client.login(config.eboekhouden.username, config.eboekhouden.password)
                if not success:
                    self.logger.error("Failed to login to e-boekhouden")
                    return None
            except Exception as e:
                self.logger.error(f"Error during e-boekhouden login: {e}")
                return None
        return self._client
    
    def get_events(self, year: int) -> list[Dict[str, Any]]:
        """Get events from database for the specified year."""
        return get_events(year)
    
    def load_schema(self) -> Dict[str, Any]:
        """Load and return the JSON schema for validation."""
        return load_json_schema('schemas/events.schema.json')
    
    def validate_events(self, events: list, schema: Dict[str, Any]) -> bool:
        """Validate events against the schema."""
        return validate_events(events, schema)
    
    def save_events(self, events: list[Dict[str, Any]], timestamp: datetime, source: str = "database") -> Path:
        """Save events to a JSON file."""
        prefix = "database" if source == "database" else "e-boekhouden"
        filename = f"{prefix}_events_{timestamp.strftime('%Y%m%d_%H%M%S')}.json"
        output_path = config.directories.output_dir / filename
        
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(events, f, indent=2, ensure_ascii=False)
        
        return output_path
    
    def cleanup(self) -> None:
        """Cleanup resources."""
        if self._client:
            self._client.close()
            self._client = None 