from playwright.sync_api import Page, Frame, sync_playwright, TimeoutError, ElementHandle
import logging
from typing import Optional, Dict, Any
import os
from datetime import datetime
import pytz
import json
from src.logging_config import get_logger, log_dict
from config import config

class EBoekhoudenClient:
    def __init__(self):
        """Initialize the client."""
        # Initialize component loggers
        self.browser_logger = get_logger('browser')
        self.network_logger = get_logger('network')
        self.business_logger = get_logger('business')
        
        self._page = None
        self._browser = None
        self._playwright = None
        # Ensure temp/screenshots directory exists
        os.makedirs(config.directories.screenshots_dir, exist_ok=True)
        
        # Start the browser and create a context
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=config.browser.headless,
            slow_mo=config.browser.slow_mo,
            args=['--disable-extensions', '--disable-plugins']
        )
        
        self._context = self._browser.new_context(
            user_agent=config.browser.user_agent,
            viewport={'width': config.browser.viewport_width, 'height': config.browser.viewport_height},
            ignore_https_errors=True,
            java_script_enabled=True,
            bypass_csp=True,
            storage_state=None,
            accept_downloads=True,
            strict_selectors=True,
            service_workers='block'
        )
        
        # Clear cookies only during initialization
        self._context.clear_cookies()
        self._page = self._context.new_page()
        self._page.set_default_timeout(config.browser.default_timeout)
        
        self.browser_logger.info("Browser initialized with custom configuration")
    
    def _take_screenshot(self, name: str):
        """Take a screenshot and save it in the temp/screenshots directory."""
        screenshot_path = os.path.join(config.directories.screenshots_dir, f"{name}.png")
        self._page.screenshot(path=screenshot_path)
    
    def login(self, username: str, password: str) -> bool:
        """Log into e-boekhouden.nl using provided credentials."""
        self.business_logger.info("Starting login process...")
        
        try:
            self._page.goto(config.eboekhouden.login_url, wait_until='domcontentloaded')
            self.network_logger.info(f"Navigated to {config.eboekhouden.login_url}")
            
            self.browser_logger.info("Looking for login form...")
            self._page.wait_for_selector('frame[name="mainframe"]', state='attached', strict=False)
            
            login_frame = self._find_login_frame()
            if not login_frame:
                self.browser_logger.error("Could not find login form")
                self._take_screenshot("error")
                return False
            
            return self._perform_login(login_frame, username, password)
            
        except TimeoutError as e:
            self.network_logger.error(f"Timeout error during login: {str(e)}")
            self._take_screenshot("timeout_error")
            return False
        except Exception as e:
            self.business_logger.error(f"Unexpected error during login: {str(e)}")
            self._take_screenshot("unexpected_error")
            return False
    
    def _find_login_frame(self) -> Optional[Frame]:
        """Find the login frame in the page."""
        max_attempts = config.retry.max_attempts
        attempt = 0
        
        while attempt < max_attempts:
            for frame in self._page.frames:
                if "inloggen.asp" in frame.url:
                    self.browser_logger.info(f"Found login frame on attempt {attempt + 1}")
                    return frame
            attempt += 1
            if attempt < max_attempts:
                self.browser_logger.info(f"Login frame not found, attempt {attempt}/{max_attempts}")
                self._page.wait_for_timeout(config.retry.delay_ms)
        
        self.browser_logger.error(f"Login frame not found after {max_attempts} attempts")
        return None
    
    def _save_page_content(self, name: str, frame: Optional[Frame] = None):
        """Save the page or frame content to a file for debugging."""
        if self.browser_logger.getEffectiveLevel() <= logging.DEBUG:
            try:
                content = frame.content() if frame else self._page.content()
                with open(os.path.join("temp", f"{name}.html"), "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                self.browser_logger.warning(f"Could not save page content for {name}: {str(e)}")
    
    def _perform_login(self, login_frame: Frame, username: str, password: str) -> bool:
        """Perform the actual login with provided credentials."""
        try:
            self.browser_logger.info("Filling login credentials...")
            username_field = login_frame.wait_for_selector("input[name='txtEmail']", state='visible', timeout=3000)
            password_field = login_frame.wait_for_selector("input[name='txtWachtwoord']", state='visible', timeout=3000)
            
            if not username_field or not password_field:
                self.browser_logger.error("Login form elements not found")
                self._take_screenshot("error")
                return False
            
            username_field.fill(username)
            password_field.fill(password)
            
            login_button = login_frame.wait_for_selector("input.act-btn[name='submit1']", timeout=3000)
            if not login_button:
                self.browser_logger.error("Could not find login button")
                self._take_screenshot("error")
                return False
            
            self.browser_logger.info("Attempting login...")
            login_button.click()
            
            # Wait for the page to load after login
            self._page.wait_for_load_state('networkidle', timeout=10000)
            
            # Wait for the frames to appear, indicating successful login
            self._page.wait_for_selector("frame[name='menuframe']", state='attached', timeout=8000)
            self._page.wait_for_selector("frame[name='mainframe']", state='attached', timeout=8000)
            
            # Save the page content after login
            self._save_page_content("after_login")
            
            self.browser_logger.info("Login successful!")
            return True
            
        except Exception as e:
            self.browser_logger.error(f"Login failed: {str(e)}")
            self._take_screenshot("login_error")
            return False
    
    def close(self):
        """Clean up resources."""
        try:
            if self._page:
                self._page.close()
            if self._context:
                self._context.close()
            if self._browser:
                self._browser.close()
            if self._playwright:
                self._playwright.stop()
        except Exception as e:
            self.browser_logger.error(f"Error during cleanup: {e}")
    
    def fetch_hours(self, year: int) -> dict:
        """Fetch hour registrations for a given year."""
        self.business_logger.info(f"Fetching hours for year {year}")
        
        # Navigate to the hours overview page
        self._page.goto("https://secure20.e-boekhouden.nl/uren/overzicht")
        self._page.wait_for_load_state('networkidle')
        
        # Save initial state for debugging
        self._save_page_content("initial_overview_state")
        
        try:
            # Wait for the main content to be visible
            content = self._wait_for_main_content()
            if not content:
                return {}
            
            # Find and click the year radio button
            self.browser_logger.info("Looking for year radio button")
            max_attempts = 60
            attempt = 0
            year_radio = None
            
            while attempt < max_attempts and not year_radio:
                try:
                    year_radio = self._page.locator('input[type="radio"][value="jaar"]').first
                    if year_radio:
                        self.browser_logger.info(f"Found year radio button on attempt {attempt + 1}")
                        year_radio.click()
                        break
                except Exception:
                    pass
                
                attempt += 1
                if attempt < max_attempts:
                    self.browser_logger.info(f"Year radio button not found, attempt {attempt}/{max_attempts}")
                    self._page.wait_for_timeout(100)
            
            if not year_radio:
                self.browser_logger.error("Year radio button not found after max attempts")
                self._save_page_content("year_radio_not_found")
                self._page.screenshot(path="error_year_radio_not_found.png")
                return {}
            
            # Find and select the year from dropdown with retry
            self.browser_logger.info(f"Selecting year {year}")
            attempt = 0
            year_select = None
            
            while attempt < max_attempts and not year_select:
                try:
                    # Try to find enabled dropdown
                    year_select = self._page.wait_for_selector('select.form-select.rect#input-year:not([disabled])', 
                                                             state='visible',
                                                             timeout=100)
                    if year_select:
                        self.browser_logger.info(f"Found enabled year dropdown on attempt {attempt + 1}")
                        break
                except TimeoutError:
                    pass
                
                attempt += 1
                if attempt < max_attempts:
                    self.browser_logger.info(f"Year dropdown not found or not enabled, attempt {attempt}/{max_attempts}")
                    self._page.wait_for_timeout(100)
            
            if not year_select:
                self.browser_logger.error("Year dropdown not found or not enabled after max attempts")
                self._save_page_content("year_dropdown_not_found")
                self._page.screenshot(path="error_year_dropdown_not_found.png")
                return {}
            
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
                self.browser_logger.error(f"Year {year} not found in dropdown")
                self._save_page_content("year_not_found")
                self._page.screenshot(path="error_year_not_found.png")
                return {}
            
            self.browser_logger.info(f"Selecting year value: {target_value}")
            year_select.select_option(target_value)
            
            # Click the "Verder" button to confirm selection
            if not self._click_verder_button():
                return {}
            
            # Wait for table to be visible
            table = self._wait_for_table()
            if not table:
                return {}
            
            # Extract data from table - use a single locator for better performance
            rows = self._page.locator('app-grid table.table-v1 tbody tr')
            
            # Wait a bit for all rows to load
            self._page.wait_for_timeout(500)
            
            count = rows.count()
            if count == 0:
                self.browser_logger.error("No rows found in table")
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
                self.browser_logger.info(f"Date: {registration['date']}, Employee: {registration['employee']}, "
                             f"Project: {registration['project']}, Activity: {registration['activity']}, "
                             f"Hours: {registration['hours']}, KM: {registration['kilometers']}, "
                             f"Description: {registration['description']}")
            
            self.browser_logger.info(f"Found {len(registrations)} hour registrations")
            return {'year': year, 'data': registrations}
            
        except Exception as e:
            self.browser_logger.error(f"Failed to fetch hours: {str(e)}")
            self._save_page_content("error_state")
            self._page.screenshot(path="error_fetch_hours.png")
            return {}

    def _handle_autocomplete(self, input_id: str, value: str, timeout: int = 10000):
        """Handle filling and selecting from an autocomplete field."""
        input_selector = f'input#{input_id}-AutocompletePickerInput'
        
        # Wait for and fill input
        input_element = self._page.wait_for_selector(input_selector, state='visible', timeout=timeout)
        if not input_element:
            raise Exception(f"Could not find input field {input_id}")
            
        # Clear existing value and fill
        input_element.click()
        input_element.fill('')  # Clear first
        input_element.fill(value)
        
        # Wait a bit for the dropdown to appear
        self._page.wait_for_timeout(1000)
        
        # Press Enter to select the first matching item
        input_element.press('Enter')
        
        # Wait a bit for the selection to be processed
        self._page.wait_for_timeout(500)

    def add_hours(self) -> bool:
        """Navigate to the add hours page and fill in the hour registration."""
        self.browser_logger.info("Navigating to add hours page")
        
        try:
            # First navigate to the hours overview page
            self._page.goto("https://secure20.e-boekhouden.nl/uren/overzicht")
            self._page.wait_for_load_state('networkidle')
            
            # Look for the "Toevoegen" button with the specific structure
            add_button = self._page.locator('app-target-link a:has(app-icon[name="plus"]) >> text=Toevoegen').first
            
            if not add_button:
                self.browser_logger.error("Add button not found")
                self._save_page_content("add_button_not_found")
                self._page.screenshot(path=os.path.join("temp", "screenshots", "add_button_not_found.png"))
                return False
            
            self.browser_logger.info("Found add button, clicking...")
            add_button.click()
            
            # Wait for navigation to complete and form to be visible
            self._page.wait_for_load_state('networkidle')
            self._page.wait_for_selector('form', state='visible')
            
            # Fill in the date (2023-01-01)
            self.browser_logger.info("Filling in date...")
            date_input = self._page.locator('input#datum')
            date_input.fill('01-01-2023')
            date_input.press('Tab')  # To ensure date is accepted
            
            # Handle all autocomplete fields
            self.browser_logger.info("Selecting employee...")
            self._handle_autocomplete('medewerkerId', 'Dave Bieleveld')
            
            self.browser_logger.info("Selecting project...")
            self._handle_autocomplete('projectId', 'Bedrijfsvoering')
            
            self.browser_logger.info("Selecting activity...")
            self._handle_autocomplete('activiteitId', 'Intern - Ontwikkelen')
            
            # Fill in hours (8)
            self.browser_logger.info("Filling in hours...")
            hours_input = self._page.locator('input#aantalUren')
            hours_input.fill('8')
            
            # Fill in comments with current timestamp
            self.browser_logger.info("Adding timestamp comment...")
            comments_input = self._page.locator('textarea#opmerkingen')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comments_input.fill(f"Test entry - Created at: {timestamp}")
            
            # Click save button
            self.browser_logger.info("Saving entry...")
            save_button = self._page.locator('button.button.form-submit:has-text("Opslaan")')
            save_button.click()
            
            # Wait for save to complete
            self._page.wait_for_load_state('networkidle')
            self._save_page_content("after_save")
            
            return True
            
        except Exception as e:
            self.browser_logger.error(f"Failed to add hours: {str(e)}")
            self._save_page_content("error_add_hours")
            self._page.screenshot(path=os.path.join("temp", "screenshots", "error_add_hours.png"))
            return False 

    def add_hours_direct(self) -> bool:
        """Navigate directly to the add hours page using the menu and fill in the hour registration."""
        self.browser_logger.info("Navigating directly to add hours page")
        
        try:
            # Navigate directly to the add hours page
            self._page.goto("https://secure20.e-boekhouden.nl/uren/overzicht/0")
            self._page.wait_for_load_state('networkidle')
            
            # Wait for form to be visible
            self._page.wait_for_selector('form', state='visible')
            
            # Fill in the date (2023-01-01)
            self.browser_logger.info("Filling in date...")
            date_input = self._page.locator('input#datum')
            date_input.fill('01-01-2023')
            date_input.press('Tab')  # To ensure date is accepted
            
            # Handle all autocomplete fields
            self.browser_logger.info("Selecting employee...")
            self._handle_autocomplete('medewerkerId', 'Dave Bieleveld')
            
            self.browser_logger.info("Selecting project...")
            self._handle_autocomplete('projectId', 'Bedrijfsvoering')
            
            self.browser_logger.info("Selecting activity...")
            self._handle_autocomplete('activiteitId', 'Intern - Ontwikkelen')
            
            # Fill in hours (8)
            self.browser_logger.info("Filling in hours...")
            hours_input = self._page.locator('input#aantalUren')
            hours_input.fill('8')
            
            # Fill in comments with current timestamp
            self.browser_logger.info("Adding timestamp comment...")
            comments_input = self._page.locator('textarea#opmerkingen')
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            comments_input.fill(f"Test entry (direct) - Created at: {timestamp}")
            
            # Click save button
            self.browser_logger.info("Saving entry...")
            save_button = self._page.locator('button.button.form-submit:has-text("Opslaan")')
            save_button.click()
            
            # Wait for save to complete
            self._page.wait_for_load_state('networkidle')
            self._save_page_content("after_save_direct")
            
            return True
            
        except Exception as e:
            self.browser_logger.error(f"Failed to add hours (direct): {str(e)}")
            self._save_page_content("error_add_hours_direct")
            self._page.screenshot(path=os.path.join("temp", "screenshots", "error_add_hours_direct.png"))
            return False 

    def download_hours_xls(self, year: int) -> tuple[str, list[dict]]:
        """Download hours overview as XLS file for a given year and convert to JSON.
        
        Returns:
            Tuple of (xls_file_path, list of event dictionaries)
        """
        self.browser_logger.info(f"Downloading hours XLS for year {year}")
        
        try:
            # Navigate to hours overview - only wait for domcontentloaded since we'll wait for content after
            self._page.goto("https://secure20.e-boekhouden.nl/uren/overzicht", wait_until='domcontentloaded')
            
            # Wait for the main content to be visible
            content = self._wait_for_main_content()
            if not content:
                return "", []
            
            # Find and click the year radio button
            self.browser_logger.info("Looking for year radio button")
            max_attempts = 60
            attempt = 0
            year_radio = None
            
            while attempt < max_attempts and not year_radio:
                try:
                    year_radio = self._page.locator('input[type="radio"][value="jaar"]').first
                    if year_radio:
                        self.browser_logger.info(f"Found year radio button on attempt {attempt + 1}")
                        year_radio.click()
                        break
                except Exception:
                    pass
                
                attempt += 1
                if attempt < max_attempts:
                    self.browser_logger.info(f"Year radio button not found, attempt {attempt}/{max_attempts}")
                    self._page.wait_for_timeout(100)
            
            if not year_radio:
                self.browser_logger.error("Year radio button not found after max attempts")
                self._save_page_content("year_radio_not_found")
                self._page.screenshot(path="error_year_radio_not_found.png")
                return "", []
            
            # Find and select the year from dropdown with retry
            self.browser_logger.info(f"Selecting year {year}")
            attempt = 0
            year_select = None
            
            while attempt < max_attempts and not year_select:
                try:
                    # Try to find enabled dropdown
                    year_select = self._page.wait_for_selector('select.form-select.rect#input-year:not([disabled])', 
                                                             state='visible',
                                                             timeout=100)
                    if year_select:
                        self.browser_logger.info(f"Found enabled year dropdown on attempt {attempt + 1}")
                        break
                except TimeoutError:
                    pass
                
                attempt += 1
                if attempt < max_attempts:
                    self.browser_logger.info(f"Year dropdown not found or not enabled, attempt {attempt}/{max_attempts}")
                    self._page.wait_for_timeout(100)
            
            if not year_select:
                self.browser_logger.error("Year dropdown not found or not enabled after max attempts")
                self._save_page_content("year_dropdown_not_found")
                self._page.screenshot(path="error_year_dropdown_not_found.png")
                return "", []
            
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
                self.browser_logger.error(f"Year {year} not found in dropdown")
                self._save_page_content("year_not_found")
                self._page.screenshot(path="error_year_not_found.png")
                return "", []
            
            self.browser_logger.info(f"Selecting year value: {target_value}")
            year_select.select_option(target_value)
            
            # Click the "Verder" button to confirm selection
            if not self._click_verder_button():
                return "", []
            
            # Wait for table to be visible
            table = self._wait_for_table()
            if not table:
                return "", []
                
            # Enable downloads in this context
            self._context.set_default_timeout(30000)  # Increase timeout for download
            self._context.set_default_navigation_timeout(30000)
            
            # Create output directory if it doesn't exist
            output_dir = "output"
            os.makedirs(output_dir, exist_ok=True)
            
            # Setup download handling with timestamp
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            download_path = os.path.join(output_dir, f"e-boekhouden_events_{year}_{timestamp}.xls")
            
            # Click the export button and wait for download
            self.browser_logger.info("Looking for export button")
            with self._page.expect_download() as download_info:
                # Try to find the export button using multiple selectors
                selectors = [
                    'div.ng-star-inserted app-icon[title="Exporteren naar Excel"]',
                    'app-icon[title="Exporteren naar Excel"]',
                    'app-icon[name="file-type-xls"]'
                ]
                
                max_attempts = 1000
                attempt = 0
                container = None
                
                while attempt < max_attempts and not container:
                    for selector in selectors:
                        try:
                            container = self._page.wait_for_selector(selector, 
                                                                   state='visible')  # Removed timeout
                            if container:
                                self.browser_logger.info(f"Found export button with selector: {selector} on attempt {attempt + 1}")
                                break
                        except TimeoutError:
                            pass
                    
                    if not container:
                        attempt += 1
                        if attempt < max_attempts:
                            self.browser_logger.info(f"Export button not found, attempt {attempt}/{max_attempts}")
                            self._page.wait_for_timeout(100)  # Wait 500ms before next attempt
                
                if not container:
                    self.browser_logger.error(f"Export button container not found after {max_attempts} attempts")
                    self._save_page_content("export_button_container_not_found")
                    self._page.screenshot(path="error_export_button_container_not_found.png")
                    return "", []
                
                self.browser_logger.info("Clicking export button")
                container.click()
                
                # Wait for the download to start and complete
                self.browser_logger.info("Waiting for download to start...")
                download = download_info.value
                
                # Save downloaded file
                self.browser_logger.info("Saving downloaded file...")
                download.save_as(download_path)
                
                # Verify file exists and has content
                if os.path.exists(download_path):
                    file_size = os.path.getsize(download_path)
                    self.browser_logger.info(f"Downloaded file saved to: {download_path} (size: {file_size} bytes)")
                    if file_size > 0:
                        # Parse XLS file into events
                        events = self._parse_hours_xls(download_path)
                        
                        # Save parsed events as JSON
                        json_path = os.path.join(output_dir, f"e-boekhouden_events_{year}_{timestamp}.json")
                        with open(json_path, 'w', encoding='utf-8') as f:
                            json.dump(events, f, indent=2, ensure_ascii=False)
                        
                        self.browser_logger.info(f"Successfully parsed {len(events)} events from XLS and saved to {json_path}")
                        return download_path, events
                    else:
                        self.browser_logger.error("Downloaded file is empty")
                        return "", []
                else:
                    self.browser_logger.error("Download failed - file not found")
                    return "", []
                
        except Exception as e:
            self.browser_logger.error(f"Failed to download XLS: {str(e)}")
            self._save_page_content("error_download_xls")
            self._page.screenshot(path="error_download_xls.png")
            return "", []

    def _parse_hours_xls(self, xls_path: str) -> list[dict]:
        """Parse hours XLS file into list of event dictionaries conforming to events schema."""
        import pandas as pd
        from datetime import datetime
        import pytz
        import numpy as np
        
        self.browser_logger.info(f"Parsing XLS file: {xls_path}")
        try:
            # Read all data from the Excel file
            df = pd.read_excel(xls_path)
            
            # Find the row index where the actual data starts (after "Datum" header)
            start_idx = df.index[df.iloc[:, 0] == "Datum"].tolist()[0] + 1
            
            # Get data rows until the last non-empty row
            data_df = df.iloc[start_idx:].copy()
            data_df.columns = ["Datum", "Medewerker", "Project", "Activiteit", "Omschrijving", "Aantal uren", "Aantal km's"]
            
            # Remove rows with NaN in critical columns
            data_df = data_df.dropna(subset=["Datum", "Medewerker", "Project", "Activiteit"])
            
            events = []
            current_time = datetime.now(pytz.UTC).isoformat()
            
            for _, row in data_df.iterrows():
                try:
                    # Replace NaN with empty string for string fields
                    description = str(row["Omschrijving"]) if not pd.isna(row["Omschrijving"]) else ""
                    
                    event = {
                        "user_name": str(row["Medewerker"]),
                        "subject": f"{row['Project']} - {row['Activiteit']}",
                        "description": description,
                        "hours": float(row["Aantal uren"]),
                        "last_modified": current_time,
                        "is_deleted": False,
                        "created_at": current_time,
                        "updated_at": current_time,
                        "project": str(row["Project"]),
                        "activity": str(row["Activiteit"])
                    }
                    events.append(event)
                except Exception as e:
                    self.browser_logger.warning(f"Failed to parse row: {row.to_dict()} - Error: {str(e)}")
                    continue
            
            self.browser_logger.info(f"Successfully parsed {len(events)} events from XLS")
            return events
            
        except Exception as e:
            self.browser_logger.error(f"Failed to parse XLS file: {str(e)}")
            return [] 

    def _wait_for_table(self) -> Optional[ElementHandle]:
        """Wait for the table to be visible with retry mechanism."""
        max_attempts = 60
        attempt = 0
        table = None
        
        while attempt < max_attempts and not table:
            try:
                table = self._page.wait_for_selector('app-grid table.table-v1', 
                                                   state='visible',
                                                   timeout=100)
                if table:
                    self.browser_logger.info(f"Found table on attempt {attempt + 1}")
                    break
            except TimeoutError:
                pass
            
            attempt += 1
            if attempt < max_attempts:
                self.browser_logger.info(f"Table not found, attempt {attempt}/{max_attempts}")
                self._page.wait_for_timeout(100)
        
        if not table:
            self.browser_logger.error("Table not found after max attempts")
            self._save_page_content("table_not_found")
            self._page.screenshot(path="error_table_not_found.png")
        
        return table

    def _click_verder_button(self) -> bool:
        """Click the Verder button with retry mechanism."""
        max_attempts = 60
        attempt = 0
        success = False
        
        while attempt < max_attempts and not success:
            try:
                verder_button = self._page.locator('button.button.form-submit span:has-text("Verder")')
                if verder_button:
                    self.browser_logger.info(f"Found Verder button on attempt {attempt + 1}")
                    verder_button.click()
                    
                    # Wait for network activity to settle
                    try:
                        self._page.wait_for_load_state('networkidle', timeout=1000)
                        success = True
                        break
                    except TimeoutError:
                        pass
            except Exception:
                pass
            
            attempt += 1
            if attempt < max_attempts:
                self.browser_logger.info(f"Verder button not clicked successfully, attempt {attempt}/{max_attempts}")
                self._page.wait_for_timeout(100)
        
        if not success:
            self.browser_logger.error("Failed to click Verder button after max attempts")
            self._save_page_content("verder_button_error")
            self._page.screenshot(path="error_verder_button.png")
        
        return success

    def _wait_for_main_content(self) -> Optional[ElementHandle]:
        """Wait for main content to be visible with retry mechanism."""
        max_attempts = 60
        attempt = 0
        content = None
        
        while attempt < max_attempts and not content:
            try:
                content = self._page.wait_for_selector('app-grid', 
                                                     state='visible',
                                                     timeout=100)
                if content:
                    self.browser_logger.info(f"Found main content on attempt {attempt + 1}")
                    break
            except TimeoutError:
                pass
            
            attempt += 1
            if attempt < max_attempts:
                self.browser_logger.info(f"Main content not found, attempt {attempt}/{max_attempts}")
                self._page.wait_for_timeout(100)
        
        if not content:
            self.browser_logger.error("Main content not found after max attempts")
            self._save_page_content("content_not_found")
            self._page.screenshot(path="error_content_not_found.png")
        
        return content 