import pytest
from unittest.mock import Mock, patch, MagicMock
from playwright.sync_api import Page, Frame, ElementHandle, TimeoutError
from src.eboekhouden import EBoekhoudenClient
import os
import json
from datetime import datetime
import pandas as pd
import pytz

@pytest.fixture
def mock_playwright():
    """Mock the playwright context and browser."""
    with patch('src.eboekhouden.sync_playwright') as mock_pw:
        playwright_instance = MagicMock()
        browser_instance = MagicMock()
        context_instance = MagicMock()
        page_instance = MagicMock()
        
        # Setup the chain of mock objects
        mock_pw.return_value.start.return_value = playwright_instance
        playwright_instance.chromium.launch.return_value = browser_instance
        browser_instance.new_context.return_value = context_instance
        context_instance.new_page.return_value = page_instance
        
        yield {
            'playwright': playwright_instance,
            'browser': browser_instance,
            'context': context_instance,
            'page': page_instance
        }

@pytest.fixture
def client(mock_playwright):
    """Create a client instance with mocked playwright."""
    client = EBoekhoudenClient()
    yield client
    client.close()

def test_init(mock_playwright, client):
    """Test client initialization."""
    # Verify browser was launched with correct arguments
    mock_playwright['playwright'].chromium.launch.assert_called_once()
    launch_args = mock_playwright['playwright'].chromium.launch.call_args[1]
    assert 'headless' in launch_args
    assert 'slow_mo' in launch_args
    assert '--disable-extensions' in launch_args['args']
    
    # Verify context was created
    mock_playwright['browser'].new_context.assert_called_once()
    context_args = mock_playwright['browser'].new_context.call_args[1]
    assert 'user_agent' in context_args
    assert 'viewport' in context_args
    
    # Verify page was created
    mock_playwright['context'].new_page.assert_called_once()

def test_login_success(client, mock_playwright):
    """Test successful login."""
    # Mock frame finding
    login_frame = MagicMock()
    mock_playwright['page'].frames = [login_frame]
    login_frame.url = "inloggen.asp"
    
    # Mock form elements
    username_field = MagicMock()
    password_field = MagicMock()
    login_button = MagicMock()
    login_frame.wait_for_selector.side_effect = [username_field, password_field, login_button]
    
    # Call login
    result = client.login("test_user", "test_pass")
    
    # Verify interactions
    assert result is True
    username_field.fill.assert_called_once_with("test_user")
    password_field.fill.assert_called_once_with("test_pass")
    login_button.click.assert_called_once()

def test_login_failure_no_frame(client, mock_playwright):
    """Test login failure when frame is not found."""
    # Mock empty frames list
    mock_playwright['page'].frames = []
    
    # Call login
    result = client.login("test_user", "test_pass")
    
    # Verify failure
    assert result is False

def test_download_hours_xls_success(client, mock_playwright, tmp_path):
    """Test successful XLS download."""
    # Create a temporary Excel file
    test_df = pd.DataFrame({
        'Datum': ['2023-01-01'],
        'Medewerker': ['Test Employee'],
        'Project': ['Test Project'],
        'Activiteit': ['Test Activity'],
        'Omschrijving': ['Test Description'],
        'Aantal uren': [8],
        'Aantal km\'s': [0]
    })
    temp_xls = tmp_path / "test.xls"
    test_df.to_excel(temp_xls, index=False)
    
    # Mock year dropdown evaluation
    year_select = MagicMock()
    year_select.evaluate.return_value = [
        {'value': '1:2023', 'text': '2023'}
    ]
    
    # Mock successful element finding for year radio
    year_radio = MagicMock()
    mock_playwright['page'].locator.return_value.first = year_radio
    
    # Mock selectors
    mock_playwright['page'].wait_for_selector.side_effect = [
        MagicMock(),  # For mainframe
        year_select,  # For year dropdown
        MagicMock(),  # For table
        MagicMock()   # For export button
    ]
    
    # Mock the verder button and export button
    verder_button = MagicMock()
    export_button = MagicMock()
    mock_playwright['page'].locator.side_effect = [
        verder_button,  # For verder button
        export_button   # For export button
    ]
    
    # Mock download
    mock_download = MagicMock()
    mock_download.save_as = MagicMock()
    
    # Setup the download context manager
    mock_context_manager = MagicMock()
    mock_context_manager.__enter__.return_value = mock_download
    mock_context_manager.__exit__.return_value = None
    mock_playwright['page'].expect_download.return_value = mock_context_manager
    
    # Mock file existence check and pandas read
    with patch('os.path.exists') as mock_exists, \
         patch('os.path.getsize') as mock_size, \
         patch('pandas.read_excel') as mock_read_excel, \
         patch('os.makedirs') as mock_makedirs:
        
        mock_exists.return_value = True
        mock_size.return_value = 1000  # Non-zero file size
        mock_makedirs.return_value = None
        
        # Create test DataFrame with header row
        header_df = pd.DataFrame({
            'Datum': ['Datum', '2023-01-01'],
            'Medewerker': ['Medewerker', 'Test Employee'],
            'Project': ['Project', 'Test Project'],
            'Activiteit': ['Activiteit', 'Test Activity'],
            'Omschrijving': ['Omschrijving', 'Test Description'],
            'Aantal uren': ['Aantal uren', 8],
            'Aantal km\'s': ['Aantal km\'s', 0]
        })
        mock_read_excel.return_value = header_df
        
        # Mock the export button click to trigger download
        def click_and_download():
            mock_download.save_as.assert_not_called()  # Not called yet
            mock_download.save_as(str(tmp_path / "test.xls"))
            return True
        
        export_button.click.side_effect = click_and_download
        
        # Call download_hours_xls
        result_path, events = client.download_hours_xls(2023)
    
    # Verify download was attempted
    assert mock_download.save_as.called
    assert len(events) == 1  # Should have one event from our test data
    assert events[0]['user_name'] == 'Test Employee'
    assert events[0]['project'] == 'Test Project'
    assert events[0]['activity'] == 'Test Activity'
    assert events[0]['hours'] == 8.0
    assert not events[0]['is_deleted']

def test_add_hours_success(client, mock_playwright):
    """Test successful hours addition."""
    # Mock form elements
    mock_playwright['page'].locator.return_value = MagicMock()
    mock_playwright['page'].wait_for_selector.return_value = MagicMock()
    
    # Call add_hours
    result = client.add_hours()
    
    # Verify success
    assert result is True
    
    # Verify form interactions
    mock_playwright['page'].goto.assert_called_with("https://secure20.e-boekhouden.nl/uren/overzicht")

def test_close(client, mock_playwright):
    """Test client cleanup."""
    client.close()
    
    # Verify all resources were cleaned up
    mock_playwright['page'].close.assert_called_once()
    mock_playwright['context'].close.assert_called_once()
    mock_playwright['browser'].close.assert_called_once()
    mock_playwright['playwright'].stop.assert_called_once()

def test_parse_hours_xls(client, tmp_path):
    """Test XLS parsing functionality."""
    # Create a test Excel file
    test_data = {
        'Datum': ['Datum', '2023-01-01'],
        'Medewerker': ['Medewerker', 'Test Employee'],
        'Project': ['Project', 'Test Project'],
        'Activiteit': ['Activiteit', 'Test Activity'],
        'Omschrijving': ['Omschrijving', 'Test Description'],
        'Aantal uren': ['Aantal uren', 8],
        'Aantal km\'s': ['Aantal km\'s', 0]
    }
    df = pd.DataFrame(test_data)
    test_file = tmp_path / "test.xls"
    df.to_excel(test_file, index=False)
    
    # Parse the file
    events = client._parse_hours_xls(str(test_file))
    
    # Verify parsed data
    assert len(events) == 1
    assert events[0]['user_name'] == 'Test Employee'
    assert events[0]['project'] == 'Test Project'
    assert events[0]['activity'] == 'Test Activity'
    assert events[0]['hours'] == 8.0
    assert events[0]['description'] == 'Test Description'
    assert not events[0]['is_deleted'] 