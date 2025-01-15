from robocorp.tasks import task
import os
from dotenv import load_dotenv
import logging
from src.eboekhouden import EBoekhoudenClient
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Global reference to keep the client alive
_client = None

def get_credentials():
    """Get credentials from environment variables."""
    load_dotenv()
    username = os.getenv("EBOEKHOUDEN_USERNAME")
    password = os.getenv("EBOEKHOUDEN_PASSWORD")
    
    if not username or not password:
        raise ValueError(
            "Missing required environment variables. Please ensure EBOEKHOUDEN_USERNAME "
            "and EBOEKHOUDEN_PASSWORD are set in your .env file"
        )
    
    return username, password

def ensure_client():
    """Ensure we have a valid client instance."""
    global _client
    if not _client:
        username, password = get_credentials()
        _client = EBoekhoudenClient()
        if not _client.login(username, password):
            _client.close()
            _client = None
            raise Exception("Login failed")
    return _client

@task
def login_to_eboekhouden():
    """Test task to verify login functionality."""
    try:
        client = ensure_client()
        return True
    except Exception as e:
        raise Exception(f"Failed to login: {str(e)}")

@task
def fetch_hours_for_year():
    """Fetch hour registrations for a year."""
    try:
        client = ensure_client()
        if not client:
            logging.error("Failed to get client instance")
            return
        
        result = client.fetch_hours(2024)
        if not result:
            logging.error("Failed to fetch hours - no data returned")
            return
            
        if 'data' not in result:
            logging.error("Invalid response format - missing 'data' field")
            return
            
        registrations = result['data']
        logging.info(f"\nRetrieved {len(registrations)} registrations for {result['year']}:")
        
        # Batch process logs for better performance
        log_messages = []
        for reg in registrations:
            log_messages.append(
                f"Date: {reg['date']}, Employee: {reg['employee']}, Project: {reg['project']}, "
                f"Activity: {reg['activity']}, Hours: {reg['hours']}, KM: {reg['kilometers']}, "
                f"Description: {reg['description']}"
            )
        
        # Log all messages at once
        for message in log_messages:
            logging.info(message)
            
        return result
            
    except Exception as e:
        logging.error(f"Failed to fetch hours: {str(e)}")
        raise
        
    finally:
        # Don't close the client to allow for inspection
        pass 

@task
def test_add_hours():
    """Test navigating to the add hours page."""
    try:
        client = ensure_client()
        if not client:
            logging.error("Failed to get client instance")
            return False
            
        result = client.add_hours()
        if result:
            logging.info("Successfully navigated to add hours page")
        else:
            logging.error("Failed to navigate to add hours page")
        
        return result
            
    except Exception as e:
        logging.error(f"Failed to test add hours: {str(e)}")
        raise
        
    finally:
        # Don't close the client to allow for inspection
        pass 

@task
def test_add_hours_direct():
    """Test adding hours using direct navigation."""
    try:
        client = ensure_client()
        if not client:
            logging.error("Failed to get client instance")
            return False
            
        result = client.add_hours_direct()
        if result:
            logging.info("Successfully added hours using direct navigation")
        else:
            logging.error("Failed to add hours using direct navigation")
        
        return result
            
    except Exception as e:
        logging.error(f"Failed to test direct hour addition: {str(e)}")
        raise
        
    finally:
        # Don't close the client to allow for inspection
        pass 

@task
def download_hours_xls():
    """Download hours overview as XLS file."""
    try:
        client = ensure_client()
        if not client:
            logging.error("Failed to get client instance")
            return
        
        # Download hours for 2024
        xls_path = client.download_hours_xls(2024)
        if xls_path:
            logging.info(f"Successfully downloaded hours XLS to: {xls_path}")
            return xls_path
        else:
            logging.error("Failed to download hours XLS file")
            # Keep the window open for inspection on failure
            input("Press Enter to close the browser window...")
            return None
            
    except Exception as e:
        logging.error(f"Failed to download hours XLS: {str(e)}")
        # Keep the window open for inspection on error
        input("Press Enter to close the browser window...")
        raise
        
    finally:
        # Don't close the client to allow for inspection
        pass 