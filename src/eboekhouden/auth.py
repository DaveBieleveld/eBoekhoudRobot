"""Authentication functions for e-boekhouden client."""
from typing import Optional
import logging

class EBoekhoudenAuth:
    """Authentication mixin for e-boekhouden client."""

    def find_login_frame(self) -> Optional['ElementHandle']:
        """Find the login frame."""
        self.browser_logger.info("Finding login frame...")
        
        # Wait for page to load completely
        self._page.wait_for_load_state('networkidle')
        
        # Get all frames
        frames = self._page.frames
        
        # Find the login frame by URL
        login_frame = None
        for frame in frames:
            if frame.url and "inloggen.asp" in frame.url:
                login_frame = frame
                break
                
        if not login_frame:
            self.browser_logger.error("Could not find login frame")
            self.save_page_content("login_frame_not_found")
            self.take_screenshot("login_frame_not_found")
            return None

        # Check if login form elements exist
        username = login_frame.locator('input[name="txtEmail"]')
        password = login_frame.locator('input[name="txtWachtwoord"]')
        
        if username.count() == 0 or password.count() == 0:
            self.browser_logger.error("Could not find login form elements")
            self.save_page_content("login_frame_not_found")
            self.take_screenshot("login_frame_not_found")
            return None

        self.browser_logger.info("Found login frame")
        self.save_page_content("login_frame_found")
        self.take_screenshot("login_frame_found")
        return login_frame

    def perform_login(self, username: str, password: str) -> bool:
        """Perform login with given credentials."""
        self.browser_logger.info("Performing login...")

        # Navigate to login page
        self._page.goto(f"{self._config.eboekhouden.login_url}/bh/?ts=340591811462&c=homepage&SV=A")

        # Find login frame
        frame = self.find_login_frame()
        if not frame:
            self.browser_logger.error("Could not find login frame")
            return False

        try:
            # Fill username and password
            username_input = frame.locator('input[name="txtEmail"]').first
            password_input = frame.locator('input[name="txtWachtwoord"]').first
            submit_button = frame.locator('input[type="submit"]').first

            username_input.fill(username)
            password_input.fill(password)

            # Click login and wait for navigation
            submit_button.click()
            
            # Wait for page to load
            self._page.wait_for_load_state('networkidle', timeout=30000)
            
            # Wait a bit for frames to load
            self._page.wait_for_timeout(5000)

            # Check for menu elements in any frame
            for frame in self._page.frames:
                try:
                    # Try to find menu elements
                    menu = frame.locator('.eb-icon-menu-support')
                    if menu.count() > 0:
                        self.browser_logger.info("Login successful - found menu in frame")
                        return True
                        
                    # Try alternative menu element
                    menu = frame.locator('.nav-sidebar-group')
                    if menu.count() > 0:
                        self.browser_logger.info("Login successful - found nav sidebar in frame")
                        return True
                        
                except Exception as e:
                    self.browser_logger.warning(f"Error checking frame for menu: {str(e)}")
                    continue

            self.browser_logger.error("Login failed - no menu elements found in any frame")
            self.save_page_content("login_failed")
            self.take_screenshot("login_failed")
            return False

        except Exception as e:
            self.browser_logger.error(f"Error during login: {str(e)}")
            self.save_page_content("login_error")
            self.take_screenshot("login_error")
            return False 