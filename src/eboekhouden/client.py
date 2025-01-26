"""Core client class for e-boekhouden."""

import os
import logging
from datetime import datetime
from typing import Optional
from playwright.sync_api import sync_playwright, Browser, Page
from src.config import config
from .auth import EBoekhoudenAuth
from .utils import EBoekhoudenUtils
from .hours import EBoekhoudenHours
from .events import EBoekhoudenEvents

class EBoekhoudenClient(EBoekhoudenAuth, EBoekhoudenUtils, EBoekhoudenHours, EBoekhoudenEvents):
    """Client for interacting with e-boekhouden.nl."""
    
    def __init__(self, username: str, password: str):
        """Initialize client with credentials.
        
        Args:
            username: E-boekhouden username
            password: E-boekhouden password
        """
        self._username = username
        self._password = password
        self._config = config
        
        # Initialize browser components
        self._playwright = None
        self._browser = None
        self._context = None
        self._page = None
        
        # Set up logging
        self.browser_logger = logging.getLogger('browser')
        self.network_logger = logging.getLogger('network')
        self.business_logger = logging.getLogger('business')
        
        # Generate timestamp for this session
        self._timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Clean up old debug files
        self.cleanup_debug_files()
        
        # Initialize browser
        self._init_browser()
    
    def _init_browser(self):
        """Initialize browser components."""
        try:
            self._playwright = sync_playwright().start()
            
            # Launch browser
            self._browser = self._playwright.chromium.launch(
                headless=config.browser.headless,
                slow_mo=config.browser.slow_mo
            )
            
            # Create context with viewport and downloads
            self._context = self._browser.new_context(
                viewport={'width': config.browser.viewport_width, 
                         'height': config.browser.viewport_height},
                accept_downloads=True
            )
            
            # Create page with user agent and timeouts
            self._page = self._context.new_page()
            self._page.set_default_timeout(config.browser.default_timeout)
            self._page.set_default_navigation_timeout(config.browser.default_timeout)
            
            if config.browser.user_agent:
                self._context.set_extra_http_headers({
                    'User-Agent': config.browser.user_agent
                })
            
            self.browser_logger.info("Browser initialized successfully")
            
        except Exception as e:
            self.browser_logger.error(f"Failed to initialize browser: {str(e)}")
            self.cleanup()
            raise
    
    def cleanup(self):
        """Clean up browser resources."""
        try:
            if self._page:
                self._page.close()
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
                
            self.browser_logger.info("Browser resources cleaned up")
            
        except Exception as e:
            self.browser_logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self._page = None
            self._context = None
            self._browser = None
            self._playwright = None
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.cleanup()
        
    @property
    def page(self) -> Optional[Page]:
        """Get current page."""
        return self._page
        
    @property
    def browser(self) -> Optional[Browser]:
        """Get current browser."""
        return self._browser
        
    def perform_login(self) -> bool:
        """Perform login using stored credentials."""
        return super().perform_login(self._username, self._password) 