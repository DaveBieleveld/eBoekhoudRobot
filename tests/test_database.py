import pytest
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
import pyodbc
from src.database import DatabaseClient

@pytest.fixture
def mock_cursor():
    cursor = Mock()
    return cursor

@pytest.fixture
def mock_connection(mock_cursor):
    conn = MagicMock()
    conn.cursor.return_value = mock_cursor
    conn.__enter__.return_value = conn
    conn.__exit__.return_value = None
    return conn

@pytest.fixture
def mock_pyodbc():
    with patch('pyodbc.connect') as mock_connect:
        yield mock_connect

@pytest.fixture
def connection_string():
    return "DRIVER={SQL Server};SERVER=test_server;DATABASE=test_db;UID=test_user;PWD=test_pass"

@pytest.fixture
def client(mock_pyodbc, mock_connection, connection_string):
    mock_pyodbc.return_value = mock_connection
    return DatabaseClient(connection_string)

def test_init(connection_string):
    client = DatabaseClient(connection_string)
    assert client.connection_string == connection_string

def test_get_hours_data_success(client, mock_cursor):
    # Setup mock data
    mock_data = [
        (1, datetime(2024, 1, 1), 'Project A', 8.0, 'Task 1'),
        (2, datetime(2024, 1, 2), 'Project B', 6.5, 'Task 2')
    ]
    mock_cursor.fetchall.return_value = mock_data
    mock_cursor.description = [
        ('id', None, None, None, None, None, None),
        ('date', None, None, None, None, None, None),
        ('project', None, None, None, None, None, None),
        ('hours', None, None, None, None, None, None),
        ('description', None, None, None, None, None, None)
    ]

    # Call the method
    result = client.get_hours_data()

    # Verify the results
    assert len(result) == 2
    assert result[0] == {
        'id': 1,
        'date': datetime(2024, 1, 1),
        'project': 'Project A',
        'hours': 8.0,
        'description': 'Task 1'
    }

def test_get_hours_data_empty(client, mock_cursor):
    # Setup mock to return empty result
    mock_cursor.fetchall.return_value = []
    mock_cursor.description = [
        ('id', None, None, None, None, None, None),
        ('date', None, None, None, None, None, None),
        ('project', None, None, None, None, None, None),
        ('hours', None, None, None, None, None, None),
        ('description', None, None, None, None, None, None)
    ]

    # Call the method
    result = client.get_hours_data()

    # Verify the results
    assert len(result) == 0

def test_get_hours_data_connection_error(mock_pyodbc, connection_string):
    # Setup mock to raise connection error
    mock_pyodbc.side_effect = pyodbc.Error

    # Create client and test
    client = DatabaseClient(connection_string)
    with pytest.raises(pyodbc.Error):
        client.get_hours_data()

def test_get_hours_data_query_error(client, mock_cursor):
    # Setup mock to raise error during execute
    mock_cursor.execute.side_effect = pyodbc.Error

    # Test
    with pytest.raises(pyodbc.Error):
        client.get_hours_data()

def test_get_hours_data_fetch_error(client, mock_cursor):
    # Setup mock to raise error during fetchall
    mock_cursor.description = [
        ('id', None, None, None, None, None, None),
        ('date', None, None, None, None, None, None),
        ('project', None, None, None, None, None, None),
        ('hours', None, None, None, None, None, None),
        ('description', None, None, None, None, None, None)
    ]
    mock_cursor.fetchall.side_effect = pyodbc.Error

    # Test
    with pytest.raises(pyodbc.Error):
        client.get_hours_data()

def test_get_hours_data_null_values(client, mock_cursor):
    # Setup mock data with NULL values
    mock_data = [
        (1, None, None, None, None)
    ]
    mock_cursor.fetchall.return_value = mock_data
    mock_cursor.description = [
        ('id', None, None, None, None, None, None),
        ('date', None, None, None, None, None, None),
        ('project', None, None, None, None, None, None),
        ('hours', None, None, None, None, None, None),
        ('description', None, None, None, None, None, None)
    ]

    # Call the method
    result = client.get_hours_data()

    # Verify the results
    assert len(result) == 1
    assert result[0] == {
        'id': 1,
        'date': None,
        'project': None,
        'hours': None,
        'description': None
    } 