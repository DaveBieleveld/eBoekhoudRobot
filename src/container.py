from typing import Optional, Dict, Any
from pathlib import Path
import logging
import json
from datetime import datetime

from src.eboekhouden import EBoekhoudenClient
from src.logging_config import get_logger
from src.config import config
from get_db_events import get_db_events, load_json_schema, validate_events

class Container:
    """Service container for dependency injection."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self._client: Optional[EBoekhoudenClient] = None
        
    def get_eboekhouden_client(self) -> EBoekhoudenClient:
        """Get or create the e-boekhouden client and ensure it's logged in."""
        if not self._client:
            self._client = EBoekhoudenClient()
            if not self._client.login(config.eboekhouden.username, config.eboekhouden.password):
                raise RuntimeError("Failed to log into e-boekhouden")
        return self._client
    
    @property
    def client(self) -> EBoekhoudenClient:
        """Get or create the e-boekhouden client."""
        if not self._client:
            self._client = EBoekhoudenClient()
        return self._client
    
    def get_db_events(self, year: int) -> list[Dict[str, Any]]:
        """Get events from the database for a specific year."""
        return get_db_events(year)
    
    def load_schema(self) -> Dict[str, Any]:
        """Load and return the JSON schema for validation."""
        return load_json_schema('schemas/events.schema.json')
    
    def validate_events(self, events: list, schema: Dict[str, Any]) -> bool:
        """Validate events against the schema."""
        return validate_events(events, schema)
    
    def save_db_events(self, events: list[Dict[str, Any]], timestamp: datetime, source: str = "database") -> Path:
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
    
    def _check_base_data_conflicts(self, differences: dict, eb_event: dict) -> int:
        """Check for conflicts in base data (project and activity)."""
        conflicts = 0
        if "project" in differences and eb_event.get("project") is not None:
            conflicts += 1
        if "activity" in differences and eb_event.get("activity") is not None:
            conflicts += 1
        return conflicts

    def _handle_event_update(self, event_id: str, db_event: dict, eb_event: dict, stats: dict) -> None:
        """Handle the logic for updating an existing event."""
        if self.client.events_differ(db_event, eb_event):
            if eb_event.get("is_invoiced"):
                stats["conflict_events"] += 1
                self.logger.error(f"Cannot update invoiced event {event_id}")
                self.logger.error(f"Differences: {json.dumps(self.client.get_event_differences(db_event, eb_event), indent=2)}")
            else:
                differences = self.client.get_event_differences(db_event, eb_event)
                self.logger.info(f"Would update event {event_id} in e-boekhouden")
                self.logger.info(f"Differences: {json.dumps(differences, indent=2)}")
                stats["would_update"] += 1
                stats["base_data_conflicts"] += self._check_base_data_conflicts(differences, eb_event)

    def _find_orphaned_events(self, eb_events: list) -> int:
        """Find and log events in e-boekhouden without event_ids."""
        orphaned_count = 0
        for eb_event in eb_events:
            description = eb_event.get("description", "")
            if "[event_id:" not in description:
                orphaned_count += 1
                self.logger.error(f"Orphaned event in e-boekhouden: {json.dumps(eb_event, indent=2)}")
        return orphaned_count

    def _log_sync_stats(self, stats: dict) -> None:
        """Log the final synchronization statistics."""
        self.logger.info("Event comparison completed with the following results:")
        self.logger.info(f"Events that would be added: {stats['would_add']}")
        self.logger.info(f"Events that would be updated: {stats['would_update']}")
        self.logger.info(f"Orphaned events found: {stats['orphaned_events']}")
        self.logger.info(f"Conflict events (invoiced): {stats['conflict_events']}")
        self.logger.info(f"Base data conflicts: {stats['base_data_conflicts']}")

    def synchronize_events(self, db_events: list, eb_events: list, year: int, dry_run: bool = True) -> dict:
        """Synchronize events between database and e-boekhouden.
        
        Steps:
        1. Use the provided e-boekhouden events (already downloaded)
        2. Add any missing events if not in dry-run mode
        3. Download events again to verify additions
        
        Args:
            db_events: List of database events
            eb_events: List of e-boekhouden events
            year: The year to synchronize (used for verification download)
            dry_run: Whether to run in dry-run mode (default: True)
            
        Returns:
            Dictionary containing synchronization statistics
        """
        stats = {
            "would_add": 0,
            "added": 0,
            "would_update": 0,
            "orphaned_events": 0,
            "conflict_events": 0,
            "base_data_conflicts": 0,
            "verified_adds": 0
        }
        
        try:
            # Step 1: Get client and verify login
            client = self.get_eboekhouden_client()
            if not client:
                self.logger.error("Failed to get e-boekhouden client")
                return stats
                
            # Step 2: Use the provided e-boekhouden events
            initial_eb_events = eb_events
            self.logger.info(f"Using {len(initial_eb_events)} events from e-boekhouden")
            
            # Step 3: Identify events to add
            events_to_add = []
            self.logger.info("Starting to identify events to add...")
            for db_event in db_events:
                event_id = db_event.get("event_id")
                if not event_id:
                    self.logger.error(f"Database event missing event_id: {db_event}")
                    continue
                    
                # Find matching event in e-boekhouden
                eb_event = next((e for e in initial_eb_events 
                               if f"[event_id:{event_id}]" in e.get("description", "")), None)
                
                if not eb_event:
                    # New event to add
                    self.logger.info(f"Would add new event {event_id} to e-boekhouden")
                    self.logger.info(f"Event details: {json.dumps(db_event, indent=2)}")
                    events_to_add.append(db_event)
                    stats["would_add"] += 1
                else:
                    # Check if event needs updating
                    self._handle_event_update(event_id, db_event, eb_event, stats)
            
            self.logger.info(f"Found {len(events_to_add)} events to add")
            
            # Step 4: Add events if not in dry run mode
            if not dry_run and events_to_add:
                self.logger.info(f"Adding {len(events_to_add)} events to e-boekhouden...")
                for event in events_to_add:
                    self.logger.info(f"Attempting to add event {event['event_id']}...")
                    if client.add_hours_direct(event):
                        self.logger.info(f"Successfully added event {event['event_id']}")
                        stats["added"] += 1
                    else:
                        self.logger.error(f"Failed to add event {event['event_id']}")
                
                # Step 5: Re-download events to verify additions
                self.logger.info("Re-downloading events to verify additions...")
                xls_path, final_eb_events = client.download_hours_xls(year)
                if final_eb_events:
                    # Check if our added events are present
                    for event in events_to_add:
                        event_id = event['event_id']
                        if any(f"[event_id:{event_id}]" in e.get("description", "") for e in final_eb_events):
                            self.logger.info(f"Verified event {event_id} was added successfully")
                            stats["verified_adds"] += 1
                        else:
                            self.logger.error(f"Added event {event_id} not found in verification download")
                else:
                    self.logger.error("Failed to download events for verification")
            
            # Step 6: Check for orphaned events
            self.logger.info("Checking for orphaned events...")
            stats["orphaned_events"] = self._find_orphaned_events(initial_eb_events)
            
            # Log final statistics
            self._log_sync_stats(stats)
            
        except Exception as e:
            self.logger.error(f"Error during synchronization: {e}")
            # Reset all stats except orphaned_events
            stats.update({
                "would_add": 0,
                "added": 0,
                "would_update": 0,
                "base_data_conflicts": 0,
                "conflict_events": 0,
                "verified_adds": 0
            })
        
        return stats 