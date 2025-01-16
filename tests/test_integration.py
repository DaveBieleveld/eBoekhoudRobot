import pytest
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch
import main
from src.container import Container

@pytest.fixture
def mock_container(mocker):
    container = Mock(spec=Container)
    container.get_events.return_value = [
        {
            "id": 1,
            "date": "2024-01-15",
            "hours": 8,
            "description": "Test event"
        }
    ]
    container.load_schema.return_value = {
        "type": "array",
        "items": {
            "type": "object",
            "required": ["id", "date", "hours", "description"]
        }
    }
    container.validate_events.return_value = True
    container.save_events.return_value = Path("output/test_events.json")
    return container

@pytest.fixture
def mock_client(mocker):
    client = Mock()
    client.download_hours_xls.return_value = (
        Path("output/test.xls"),
        [{"id": 1, "date": "2024-01-15", "hours": 8}]
    )
    return client

def test_main_success(mock_container, mock_client, mocker):
    """Test successful execution of main program."""
    # Mock command line arguments
    mocker.patch('sys.argv', ['main.py', '--year', '2024'])
    
    # Mock container creation
    mocker.patch('main.Container', return_value=mock_container)
    mock_container.get_eboekhouden_client.return_value = mock_client
    
    # Run main program
    result = main.main()
    
    # Verify success
    assert result == 0
    
    # Verify container method calls
    mock_container.load_schema.assert_called_once()
    mock_container.get_events.assert_called_once_with(2024)
    mock_container.validate_events.assert_called_once()
    mock_container.save_events.assert_called_once()
    mock_container.get_eboekhouden_client.assert_called_once()
    mock_container.cleanup.assert_called_once()

def test_main_schema_load_failure(mock_container, mocker):
    """Test main program handling schema load failure."""
    mocker.patch('sys.argv', ['main.py', '--year', '2024'])
    mocker.patch('main.Container', return_value=mock_container)
    
    # Simulate schema load failure
    mock_container.load_schema.side_effect = Exception("Schema load failed")
    
    result = main.main()
    
    assert result == 1
    mock_container.load_schema.assert_called_once()
    mock_container.cleanup.assert_called_once()

def test_main_events_load_failure(mock_container, mocker):
    """Test main program handling events load failure."""
    mocker.patch('sys.argv', ['main.py', '--year', '2024'])
    mocker.patch('main.Container', return_value=mock_container)
    
    # Simulate events load failure
    mock_container.get_events.side_effect = Exception("Events load failed")
    
    result = main.main()
    
    assert result == 1
    mock_container.load_schema.assert_called_once()
    mock_container.get_events.assert_called_once()
    mock_container.cleanup.assert_called_once()

def test_main_validation_failure(mock_container, mocker):
    """Test main program handling validation failure."""
    mocker.patch('sys.argv', ['main.py', '--year', '2024'])
    mocker.patch('main.Container', return_value=mock_container)
    
    # Simulate validation failure
    mock_container.validate_events.return_value = False
    
    result = main.main()
    
    assert result == 1
    mock_container.load_schema.assert_called_once()
    mock_container.get_events.assert_called_once()
    mock_container.validate_events.assert_called_once()
    mock_container.cleanup.assert_called_once()

def test_main_client_login_failure(mock_container, mocker):
    """Test main program handling e-boekhouden login failure."""
    mocker.patch('sys.argv', ['main.py', '--year', '2024'])
    mocker.patch('main.Container', return_value=mock_container)
    
    # Simulate login failure
    mock_container.get_eboekhouden_client.return_value = None
    
    result = main.main()
    
    assert result == 1
    mock_container.get_eboekhouden_client.assert_called_once()
    mock_container.cleanup.assert_called_once() 