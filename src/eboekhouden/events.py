"""Events management functions for e-boekhouden client."""

import logging
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from src.config import config
from .base import EBoekhoudenBase

class EBoekhoudenEvents(EBoekhoudenBase):
    """Events management methods for EBoekhoudenClient."""
    
    def compare_events(self, db_events: List[Dict], eb_events: List[Dict]) -> Tuple[List[Dict], List[Dict], List[Dict]]:
        """Compare events between database and e-boekhouden.
        
        Args:
            db_events: List of events from database
            eb_events: List of events from e-boekhouden
            
        Returns:
            Tuple containing:
            - List of events to add
            - List of events to update
            - List of orphaned events
        """
        events_to_add = []
        events_to_update = []
        orphaned_events = []
        
        # Track processed events to identify orphans
        processed_eb_events = set()
        
        # First pass - find matches and identify events to add/update
        for db_event in db_events:
            found_match = False
            
            for eb_event in eb_events:
                # Skip already processed events
                if eb_event['id'] in processed_eb_events:
                    continue
                    
                # Check for event_id match
                if 'event_id' in eb_event and eb_event['event_id'] == db_event['event_id']:
                    found_match = True
                    processed_eb_events.add(eb_event['id'])
                    
                    # Check if update needed
                    if self.needs_update(db_event, eb_event):
                        events_to_update.append((db_event, eb_event))
                    break
                    
                # Check for content match if no event_id
                elif self.events_match(db_event, eb_event):
                    found_match = True
                    processed_eb_events.add(eb_event['id'])
                    break
            
            if not found_match:
                events_to_add.append(db_event)
        
        # Second pass - identify orphaned events
        for eb_event in eb_events:
            if eb_event['id'] not in processed_eb_events:
                orphaned_events.append(eb_event)
        
        return events_to_add, events_to_update, orphaned_events

    def events_match(self, db_event: Dict, eb_event: Dict) -> bool:
        """Check if two events match based on content.
        
        Args:
            db_event: Event from database
            eb_event: Event from e-boekhouden
            
        Returns:
            True if events match, False otherwise
        """
        # Compare key fields
        if db_event['project'] != eb_event['project']:
            return False
            
        if db_event['activity'] != eb_event['activity']:
            return False
            
        if abs(db_event['hours'] - eb_event['hours']) > 0.01:  # Allow small difference in hours
            return False
            
        # Compare dates within 24 hours
        db_date = datetime.fromisoformat(db_event['start_date'].replace('Z', '+00:00'))
        eb_date = datetime.fromisoformat(eb_event['date'].replace('Z', '+00:00'))
        if abs((db_date - eb_date).total_seconds()) > 86400:  # 24 hours in seconds
            return False
        
        return True

    def needs_update(self, db_event: Dict, eb_event: Dict) -> bool:
        """Check if an event needs to be updated.
        
        Args:
            db_event: Event from database
            eb_event: Event from e-boekhouden
            
        Returns:
            True if event needs update, False otherwise
        """
        # Compare last modified timestamps
        db_modified = datetime.fromisoformat(db_event['last_modified'].replace('Z', '+00:00'))
        eb_modified = datetime.fromisoformat(eb_event['last_modified'].replace('Z', '+00:00'))
        
        # If database event is newer, update needed
        if db_modified > eb_modified:
            return True
        
        return False

    def parse_hours_xls(self, xls_path: str) -> List[Dict]:
        """Parse hours from XLS file into list of events.
        
        Args:
            xls_path: Path to XLS file
            
        Returns:
            List of event dictionaries
        """
        try:
            import pandas as pd
            
            # Read XLS file
            df = pd.read_excel(xls_path)
            
            # Map column names
            column_map = config.eboekhouden.table_columns
            
            events = []
            for _, row in df.iterrows():
                event = {
                    'id': str(row[column_map['id']]),
                    'user_name': str(row[column_map['user']]),
                    'project': str(row[column_map['project']]),
                    'activity': str(row[column_map['activity']]),
                    'hours': float(row[column_map['hours']]),
                    'description': str(row[column_map['description']]),
                    'date': str(row[column_map['date']]),
                    'last_modified': str(row[column_map['last_modified']]),
                    'created_at': datetime.now().isoformat()
                }
                
                # Extract event_id from description if present
                if 'event_id:' in event['description']:
                    event['event_id'] = event['description'].split('event_id:')[1].strip()
                
                events.append(event)
                
            return events
            
        except Exception as e:
            self.browser_logger.error(f"Failed to parse XLS file: {str(e)}")
            return [] 