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
    
    client = container.get_eboekhouden_client()
    assert client is None
    mock_client.login.assert_called_once()

def test_get_events(container, mock_events, mocker):
    """Test retrieving events from database."""
    mocker.patch('src.container.get_events', return_value=mock_events)
    
    events = container.get_events(2024)
    assert events == mock_events
    assert len(events) == 1
    assert events[0]["hours"] == 8

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

def test_save_events(container, mock_events, tmp_path, mocker):
    """Test saving events to JSON file."""
    # Mock config directories
    mocker.patch('src.container.config.directories.output_dir', tmp_path)
    
    timestamp = datetime(2024, 1, 15, 12, 0, 0)
    output_path = container.save_events(mock_events, timestamp)
    
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