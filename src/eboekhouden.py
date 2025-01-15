from playwright.sync_api import Page, Frame, sync_playwright, TimeoutError
import logging
from typing import Optional, Dict, Any
import os

logger = logging.getLogger(__name__)

class EBoekhoudenClient:
    def __init__(self):
        """Initialize the client."""
        self.logger = logging.getLogger(__name__)
        self._page = None
        self._browser = None
        # Ensure temp/screenshots directory exists
        os.makedirs(os.path.join("temp", "screenshots"), exist_ok=True)
        
        # Start the browser and create a context
        playwright = sync_playwright().start()
        self._browser = playwright.chromium.launch(
            headless=False,
            slow_mo=50,
            args=['--disable-extensions', '--disable-plugins']
        )
        
        self._context = self._browser.new_context(
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
            viewport={'width': 1920, 'height': 1080},
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            storage_state=None,
            accept_downloads=False,
            strict_selectors=True,
            service_workers='block'
        )
        
        # Clear cookies only during initialization
        self._context.clear_cookies()
        self._page = self._context.new_page()
        self._page.set_default_timeout(5000)
    
    def _take_screenshot(self, name: str):
        """Take a screenshot and save it in the temp/screenshots directory."""
        screenshot_path = os.path.join("temp", "screenshots", f"{name}.png")
        self._page.screenshot(path=screenshot_path)
    
    def login(self, username: str, password: str) -> bool:
        """Log into e-boekhouden.nl using provided credentials."""
        login_url = "https://secure.e-boekhouden.nl/bh/?ts=340591811462&c=homepage&SV=A"
        self.logger.info("Starting login process...")
        
        try:
            self._page.goto(login_url, wait_until='domcontentloaded')
            
            self.logger.info("Looking for login form...")
            self._page.wait_for_selector('frame[name="mainframe"]', state='attached', strict=False)
            
            login_frame = self._find_login_frame()
            if not login_frame:
                self.logger.error("Could not find login form")
                self._take_screenshot("error")
                return False
            
            return self._perform_login(login_frame, username, password)
            
        except TimeoutError as e:
            self.logger.error(f"Timeout error: {str(e)}")
            self._take_screenshot("timeout_error")
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error: {str(e)}")
            self._take_screenshot("unexpected_error")
            return False
    
    def _find_login_frame(self) -> Optional[Frame]:
        """Find the login frame in the page."""
        max_attempts = 3
        for attempt in range(max_attempts):
            for frame in self._page.frames:
                if "inloggen.asp" in frame.url:
                    return frame
            if attempt < max_attempts - 1:
                self._page.wait_for_timeout(200)
        return None
    
    def _save_page_content(self, name: str, frame: Optional[Frame] = None):
        """Save the page or frame content to a file for debugging."""
        try:
            content = frame.content() if frame else self._page.content()
            with open(os.path.join("temp", f"{name}.html"), "w", encoding="utf-8") as f:
                f.write(content)
        except Exception as e:
            self.logger.warning(f"Could not save page content for {name}: {str(e)}")
    
    def _perform_login(self, login_frame: Frame, username: str, password: str) -> bool:
        """Perform the actual login with provided credentials."""
        try:
            self.logger.info("Filling login credentials...")
            username_field = login_frame.wait_for_selector("input[name='txtEmail']", state='visible')
            password_field = login_frame.wait_for_selector("input[name='txtWachtwoord']", state='visible')
            
            if not username_field or not password_field:
                self.logger.error("Login form elements not found")
                self._take_screenshot("error")
                return False
            
            username_field.fill(username)
            password_field.fill(password)
            
            login_button = login_frame.wait_for_selector("input.act-btn[name='submit1']")
            if not login_button:
                self.logger.error("Could not find login button")
                self._take_screenshot("error")
                return False
            
            self.logger.info("Attempting login...")
            login_button.click()
            
            # Wait for the page to load after login
            self._page.wait_for_load_state('networkidle')
            
            # Wait for the frames to appear, indicating successful login
            self._page.wait_for_selector("frame[name='menuframe']", state='attached', timeout=10000)
            self._page.wait_for_selector("frame[name='mainframe']", state='attached', timeout=10000)
            
            # Save the page content after login
            self._save_page_content("after_login")
            
            self.logger.info("Login successful!")
            return True
            
        except Exception as e:
            self.logger.error(f"Login failed: {str(e)}")
            self._take_screenshot("login_error")
            return False
    
    def close(self):
        """Clean up resources."""
        # Commented out auto-closing to allow manual inspection
        # if self._context:
        #     self._context.close()
        # if self._browser:
        #     self._browser.close()
        pass

    def fetch_hours(self, year: int) -> dict:
        """Fetch hour registrations for a given year."""
        self.logger.info(f"Fetching hours for year {year}")
        
        # Navigate to the hours overview page
        self._page.goto("https://secure20.e-boekhouden.nl/uren/overzicht")
        self._page.wait_for_load_state('networkidle')
        
        # Save initial state for debugging
        self._save_page_content("initial_overview_state")
        
        try:
            # Wait for the main content to be visible
            self.logger.info("Waiting for main content to be visible")
            content = self._page.wait_for_selector('app-grid', state='visible', timeout=10000)
            if not content:
                self.logger.error("Main content not found")
                self._save_page_content("content_not_found")
                self._page.screenshot(path="error_content_not_found.png")
                return {}
            
            # Find and click the year radio button
            self.logger.info("Looking for year radio button")
            year_radio = self._page.locator('input[type="radio"][value="jaar"]').first
            if not year_radio:
                self.logger.error("Year radio button not found")
                self._save_page_content("year_radio_not_found")
                self._page.screenshot(path="error_year_radio_not_found.png")
                return {}
            
            year_radio.click()
            self._page.wait_for_timeout(2000)  # Wait for any animations
            
            # Find and select the year from dropdown
            self.logger.info(f"Selecting year {year}")
            year_select = self._page.wait_for_selector('select.form-select.rect#input-year', state='visible', timeout=5000)
            if not year_select:
                self.logger.error("Year dropdown not found")
                self._save_page_content("year_dropdown_not_found")
                self._page.screenshot(path="error_year_dropdown_not_found.png")
                return {}
            
            # Wait for the dropdown to be enabled
            self.logger.info("Waiting for year dropdown to be enabled")
            self._page.wait_for_selector('select.form-select.rect#input-year:not([disabled])', state='visible', timeout=5000)
            
            # The value format is "index: year", so we need to find the right option
            year_options = year_select.evaluate("""select => {
                const options = select.options;
                const values = [];
                for (let i = 0; i < options.length; i++) {
                    values.push({
                        value: options[i].value,
                        text: options[i].text.trim()
                    });
                }
                return values;
            }""")
            
            target_value = None
            for option in year_options:
                if str(year) == option['text'].strip():
                    target_value = option['value']
                    break
            
            if not target_value:
                self.logger.error(f"Year {year} not found in dropdown")
                self._save_page_content("year_not_found")
                self._page.screenshot(path="error_year_not_found.png")
                return {}
            
            self.logger.info(f"Selecting year value: {target_value}")
            year_select.select_option(target_value)
            
            # Click the "Verder" button to confirm selection
            self.logger.info("Clicking 'Verder' button to confirm selection")
            verder_button = self._page.locator('button.button.form-submit span:has-text("Verder")')
            verder_button.click()
            
            # Wait for table to update - use network idle instead of fixed timeout
            self._page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for table to be visible with data - use a more specific selector
            self.logger.info("Waiting for table to update")
            table_selector = 'app-grid table.table-v1 tbody tr'
            try:
                # Wait for at least one row to be visible
                self._page.wait_for_selector(table_selector, state='visible', timeout=10000, strict=False)
            except Exception as e:
                self.logger.error(f"Table not found after year selection: {str(e)}")
                self._save_page_content("table_not_found")
                self._page.screenshot(path="error_table_not_found.png")
                return {}
            
            # Extract data from table - use a single locator for better performance
            rows = self._page.locator(table_selector)
            
            # Wait a bit for all rows to load
            self._page.wait_for_timeout(500)
            
            count = rows.count()
            if count == 0:
                self.logger.error("No rows found in table")
                return {}
                
            registrations = []
            
            # Prepare all cell selectors once
            cell_selectors = {
                'date': 'td:nth-child(4)',
                'employee': 'td:nth-child(5)',
                'project': 'td:nth-child(6)',
                'activity': 'td:nth-child(7)',
                'description': 'td:nth-child(8)',
                'hours': 'td:nth-child(9)',
                'kilometers': 'td:nth-child(10)'
            }
            
            # Batch process rows
            for i in range(count):
                row = rows.nth(i)
                registration = {
                    field: row.locator(selector).text_content().strip()
                    for field, selector in cell_selectors.items()
                }
                registrations.append(registration)
                
                # Only log if debug logging is enabled
                self.logger.info(f"Date: {registration['date']}, Employee: {registration['employee']}, "
                             f"Project: {registration['project']}, Activity: {registration['activity']}, "
                             f"Hours: {registration['hours']}, KM: {registration['kilometers']}, "
                             f"Description: {registration['description']}")
            
            self.logger.info(f"Found {len(registrations)} hour registrations")
            return {'year': year, 'data': registrations}
            
        except Exception as e:
            self.logger.error(f"Failed to fetch hours: {str(e)}")
            self._save_page_content("error_state")
            self._page.screenshot(path="error_fetch_hours.png")
            return {} 