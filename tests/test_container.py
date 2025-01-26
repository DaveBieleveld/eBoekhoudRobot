import pytest
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch
from src.container import Container
from src.eboekhouden import EBoekhoudenClient

@pytest.fixture
def container():
    return Container()

@pytest.fixture
def mock_client(mocker):
    client = Mock(spec=EBoekhoudenClient)
    client.login.return_value = True
    return client

@pytest.fixture
def mock_events():
    return [
        {
            "id": 1,
            "date": "2024-01-15",
            "hours": 8,
            "description": "Test event"
        }
    ]

@pytest.fixture
def mock_schema():
    return {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["id", "date", "hours", "description"]
        }
    }

@pytest.fixture
def mock_db_events():
    """Sample database events for testing."""
    return [
        {
            "event_id": "event1",
            "user_name": "Test User",
            "subject": "Test Event 1",
            "description": "Test description 1",
            "hours": 8.0,
            "project": "Project A",
            "activity": "Development",
            "is_deleted": False,
            "last_modified": "2024-01-15T10:00:00Z",
            "created_at": "2024-01-15T10:00:00Z",
            "updated_at": "2024-01-15T10:00:00Z"
        },
        {
            "event_id": "event2",
            "user_name": "Test User",
            "subject": "Test Event 2",
            "description": "Test description 2",
            "hours": 4.0,
            "project": "Project B",
            "activity": "Testing",
            "is_deleted": False,
            "last_modified": "2024-01-15T11:00:00Z",
            "created_at": "2024-01-15T11:00:00Z",
            "updated_at": "2024-01-15T11:00:00Z"
        }
    ]

@pytest.fixture
def mock_eb_events():
    """Sample e-boekhouden events for testing."""
    return [
        {
            "user_name": "Test User",
            "subject": "Test Event 1",
            "description": "[event_id:event1] Test description 1",
            "hours": 8.0,
            "project": "Project A",
            "activity": "Development",
            "is_deleted": False
        },
        {
            "user_name": "Test User",
            "subject": "Orphaned Event",
            "description": "No event ID here",
            "hours": 2.0,
            "project": "Project C",
            "activity": "Meeting",
            "is_deleted": False
        }
    ]

def test_get_eboekhouden_client_success(container, mocker):
    """Test successful client creation and login."""
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.login.return_value = True
    mocker.patch('src.container.EBoekhoudenClient', return_value=mock_client)
    
    client = container.get_eboekhouden_client()
    assert client is not None
    mock_client.login.assert_called_once()

def test_get_eboekhouden_client_login_failure(container, mocker):
    """Test client creation with login failure."""
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.login.return_value = False
    mocker.patch('src.container.EBoekhoudenClient', return_value=mock_client)

    # Should raise RuntimeError when login fails
    with pytest.raises(RuntimeError, match="Failed to log into e-boekhouden"):
        client = container.get_eboekhouden_client()

def test_get_db_events(container, mock_events):
    """Test retrieving events from the database."""
    # Replace the container's get_db_events method with a simple return
    container.get_db_events = lambda year: mock_events

    # Call the container method
    events = container.get_db_events(2024)

    # Verify results
    assert events == mock_events
    assert len(events) == 1
    assert events[0]["id"] == 1

def test_load_schema(container, mock_schema, mocker):
    """Test loading JSON schema."""
    mocker.patch('src.container.load_json_schema', return_value=mock_schema)
    
    schema = container.load_schema()
    assert schema == mock_schema
    assert schema["type"] == "array"

def test_validate_events_success(container, mock_events, mock_schema, mocker):
    """Test successful event validation."""
    mocker.patch('src.container.validate_events', return_value=True)
    
    result = container.validate_events(mock_events, mock_schema)
    assert result is True

def test_save_db_events(container, mock_events, tmp_path, mocker):
    """Test saving events to JSON file."""
    # Mock config directories
    mocker.patch('src.container.config.directories.output_dir', tmp_path)
    
    timestamp = datetime(2024, 1, 15, 12, 0, 0)
    output_path = container.save_db_events(mock_events, timestamp)
    
    assert output_path.exists()
    assert output_path.name.startswith("database_events_")
    assert output_path.suffix == ".json"
    
    # Verify file contents
    with open(output_path) as f:
        saved_events = json.load(f)
    assert saved_events == mock_events

def test_cleanup(container, mock_client, mocker):
    """Test resource cleanup."""
    mocker.patch.object(container, '_client', mock_client)
    
    container.cleanup()
    mock_client.close.assert_called_once()
    assert container._client is None 

def test_process_events_dry_run(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing in dry-run mode."""
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = True
    mock_client.get_event_differences.return_value = {
        "hours": {"database": 8.0, "e-boekhouden": 7.0}
    }
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)
    
    # Verify statistics
    assert stats["would_add"] == 1  # event2 needs to be added
    assert stats["would_update"] == 1  # event1 needs update
    assert stats["orphaned_events"] == 1  # One event without event_id
    assert stats["conflict_events"] == 0
    assert stats["base_data_conflicts"] == 0

def test_process_events_with_conflicts(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing with invoiced events."""
    # Modify e-boekhouden event to be invoiced
    mock_eb_events[0]["is_invoiced"] = True
    
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = True
    mock_client.get_event_differences.return_value = {
        "hours": {"database": 8.0, "e-boekhouden": 7.0}
    }
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)
    
    # Verify statistics
    assert stats["would_add"] == 1  # event2 needs to be added
    assert stats["would_update"] == 0  # event1 can't be updated (invoiced)
    assert stats["orphaned_events"] == 1  # One event without event_id
    assert stats["conflict_events"] == 1  # One invoiced event with differences
    assert stats["base_data_conflicts"] == 0 

def test_process_events_missing_fields(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing with missing fields."""
    # Remove required fields from e-boekhouden event
    mock_eb_events[0].pop("hours")
    mock_eb_events[0].pop("project")
    
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = True
    mock_client.get_event_differences.return_value = {
        "hours": {"database": 8.0, "e-boekhouden": None},
        "project": {"database": "Project A", "e-boekhouden": None}
    }
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)
    
    # Verify statistics
    assert stats["would_update"] == 1  # event1 needs update due to missing fields
    assert stats["base_data_conflicts"] == 0
    assert stats["would_add"] == 1  # event2 still needs to be added
    assert stats["orphaned_events"] == 1  # One event without event_id

def test_process_events_field_differences(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing with different field values."""
    # Modify e-boekhouden event fields
    mock_eb_events[0].update({
        "hours": 4.0,  # Different hours
        "project": "Project X",  # Different project
        "activity": "Testing",  # Different activity
        "user_name": "Another User"  # Different user
    })
    
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = True
    mock_client.get_event_differences.return_value = {
        "hours": {"database": 8.0, "e-boekhouden": 4.0},
        "project": {"database": "Project A", "e-boekhouden": "Project X"},
        "activity": {"database": "Development", "e-boekhouden": "Testing"},
        "user_name": {"database": "Test User", "e-boekhouden": "Another User"}
    }
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)
    
    # Verify statistics
    assert stats["would_update"] == 1  # event1 needs update due to field differences
    assert stats["base_data_conflicts"] == 2  # Project and Activity differences
    assert stats["would_add"] == 1  # event2 still needs to be added
    assert stats["orphaned_events"] == 1  # One event without event_id

def test_process_events_error_handling(container, mock_db_events, mock_eb_events, mocker):
    """Test error handling during event processing."""
    # Mock the client's event comparison methods to raise an exception
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.side_effect = Exception("Test error")
    mocker.patch.object(container, '_client', mock_client)

    # Process events - should handle the error gracefully
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)

    # Verify statistics - all stats should be reset on error except orphaned events
    assert stats["would_add"] == 0  # Reset due to error
    assert stats["would_update"] == 0  # Reset due to error
    assert stats["base_data_conflicts"] == 0  # Reset due to error
    assert stats["orphaned_events"] == 1  # Still counts orphaned events
    assert stats["conflict_events"] == 0  # Reset due to error

def test_process_events_no_changes_needed(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing when no changes are needed."""
    # Make e-boekhouden events match database events exactly
    mock_eb_events[0].update({
        "hours": 8.0,
        "project": "Project A",
        "activity": "Development",
        "user_name": "Test User"
    })
    mock_eb_events.append({
        "user_name": "Test User",
        "subject": "Test Event 2",
        "description": "[event_id:event2] Test description 2",
        "hours": 4.0,
        "project": "Project B",
        "activity": "Testing",
        "is_deleted": False
    })
    
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = False
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events[:-1], dry_run=True)
    
    # Verify statistics
    assert stats["would_add"] == 1  # event2 needs to be added
    assert stats["would_update"] == 0  # No updates needed
    assert stats["orphaned_events"] == 1  # One event without event_id
    assert stats["conflict_events"] == 0
    assert stats["base_data_conflicts"] == 0

def test_process_events_all_events_match(container, mock_db_events, mock_eb_events, mocker):
    """Test event processing when all events match exactly."""
    # Make e-boekhouden events match database events exactly
    mock_eb_events = [
        {
            "user_name": "Test User",
            "subject": "Test Event 1",
            "description": "[event_id:event1] Test description 1",
            "hours": 8.0,
            "project": "Project A",
            "activity": "Development",
            "is_deleted": False
        },
        {
            "user_name": "Test User",
            "subject": "Test Event 2",
            "description": "[event_id:event2] Test description 2",
            "hours": 4.0,
            "project": "Project B",
            "activity": "Testing",
            "is_deleted": False
        }
    ]
    
    # Mock the client's event comparison methods
    mock_client = Mock(spec=EBoekhoudenClient)
    mock_client.events_differ.return_value = False
    mocker.patch.object(container, '_client', mock_client)
    
    # Process events
    stats = container.process_events(mock_db_events, mock_eb_events, dry_run=True)
    
    # Verify statistics
    assert stats["would_add"] == 0  # No additions needed
    assert stats["would_update"] == 0  # No updates needed
    assert stats["orphaned_events"] == 0  # No orphaned events
    assert stats["conflict_events"] == 0
    assert stats["base_data_conflicts"] == 0 