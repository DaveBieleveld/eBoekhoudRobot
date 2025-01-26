"""Hours management functions for e-boekhouden client."""

import os
import json
import logging
from typing import Optional, Tuple, List, Dict
from playwright.sync_api import ElementHandle, Page, TimeoutError
from src.config import config
from .base import EBoekhoudenBase

class EBoekhoudenHours(EBoekhoudenBase):
    """Hours management methods for EBoekhoudenClient."""
    
    def download_hours_xls(self, year: int) -> Tuple[str, List[Dict]]:
        """Download hours overview as XLS file and convert to JSON.
        
        Args:
            year: The year to download hours for
            
        Returns:
            Tuple containing:
            - Path to the downloaded XLS file
            - List of event dictionaries parsed from the file
        """
        self.browser_logger.info(f"Downloading hours for year {year}")
        
        # Navigate directly to hours overview
        self._page.goto(f"{config.eboekhouden.base_url}/uren/overzicht")
        
        # Wait for page to load completely
        self._page.wait_for_load_state('networkidle')
        self._page.wait_for_load_state('domcontentloaded')
        self._page.wait_for_timeout(config.browser.default_timeout)
        
        # Log all frames for debugging
        self.browser_logger.info("Available frames:")
        for frame in self._page.frames:
            self.browser_logger.info(f"Frame: {frame.name} - URL: {frame.url}")
            
        # Wait for main frame to load
        main_frame = self._page.frame_locator('frame[name="mainframe"]').first
        if not main_frame:
            self.browser_logger.error("Could not find main frame")
            self.save_page_content("main_frame_not_found")
            self.take_screenshot("main_frame_not_found")
            raise Exception("Could not find main frame")
            
        # Wait for year radio button
        try:
            year_radio = main_frame.wait_for_selector('input[type="radio"][value="jaar"]', state='visible', timeout=config.browser.default_timeout)
            if not year_radio:
                self.browser_logger.error("Could not find year radio button")
                self.save_page_content("year_radio_not_found")
                self.take_screenshot("year_radio_not_found")
                raise Exception("Could not find year radio button")
            year_radio.click()
        except Exception as e:
            self.browser_logger.error(f"Error clicking year radio: {str(e)}")
            self.save_page_content("year_radio_error")
            self.take_screenshot("year_radio_error")
            raise
            
        # Select year from dropdown
        try:
            year_select = main_frame.wait_for_selector('select.form-select.rect#input-year', state='visible', timeout=config.browser.default_timeout)
            if not year_select:
                self.browser_logger.error("Could not find year select")
                self.save_page_content("year_select_not_found")
                self.take_screenshot("year_select_not_found")
                raise Exception("Could not find year select")
            year_select.select_option(str(year))
        except Exception as e:
            self.browser_logger.error(f"Error selecting year: {str(e)}")
            self.save_page_content("year_select_error")
            self.take_screenshot("year_select_error")
            raise
            
        # Click confirm button
        try:
            confirm_button = main_frame.wait_for_selector('button.button.form-submit span:has-text("Verder")', state='visible', timeout=config.browser.default_timeout)
            if not confirm_button:
                self.browser_logger.error("Could not find confirm button")
                self.save_page_content("confirm_button_not_found")
                self.take_screenshot("confirm_button_not_found")
                raise Exception("Could not find confirm button")
            confirm_button.click()
        except Exception as e:
            self.browser_logger.error(f"Error clicking confirm button: {str(e)}")
            self.save_page_content("confirm_button_error")
            self.take_screenshot("confirm_button_error")
            raise
            
        # Wait for export button and click it
        try:
            export_button = main_frame.wait_for_selector('app-icon[title="Exporteren naar Excel"]', state='visible', timeout=config.browser.default_timeout)
            if not export_button:
                self.browser_logger.error("Could not find export button")
                self.save_page_content("export_button_not_found")
                self.take_screenshot("export_button_not_found")
                raise Exception("Could not find export button")

            # Wait for download
            with self._page.expect_download(timeout=config.browser.download_timeout) as download_info:
                export_button.click()
            download = download_info.value

            # Save file
            xls_path = os.path.join(config.directories.output_dir, f"e-boekhouden_events_{year}_{self._timestamp}.xls")
            download.save_as(xls_path)

            # Parse events from XLS
            events = self.parse_hours_xls(xls_path)
            return xls_path, events

        except Exception as e:
            self.browser_logger.error(f"Error downloading XLS: {str(e)}")
            self.save_page_content("download_error")
            self.take_screenshot("download_error")
            raise

    def add_hours_direct(self, event: Dict) -> bool:
        """Add hours directly to e-boekhouden using event data.
        
        Args:
            event: Dictionary containing event data
            
        Returns:
            True if successful, False otherwise
        """
        self.browser_logger.info("Navigating directly to add hours page")
        
        try:
            # Navigate to add hours page
            self._page.goto(f"{config.eboekhouden.base_url}/bh/urenregistratie_toevoegen.asp")
            self._page.wait_for_load_state('domcontentloaded')
            
            # Validate required fields
            required_fields = ['project', 'activity', 'hours', 'description']
            for field in required_fields:
                if field not in event:
                    self.browser_logger.error(f"Missing required field: {field}")
                    return False
            
            # Fill project
            self.handle_autocomplete('project', event['project'])
            
            # Fill activity
            self.handle_autocomplete('activity', event['activity'])
            
            # Fill hours
            hours_input = self._page.wait_for_selector('input[name="txtUren"]', state='visible')
            if not hours_input:
                self.browser_logger.error("Could not find hours input")
                return False
            hours_input.fill(str(event['hours']))
            
            # Fill description
            description_input = self._page.wait_for_selector('textarea[name="txtOmschrijving"]', state='visible')
            if not description_input:
                self.browser_logger.error("Could not find description input")
                return False
            
            # Add timestamp comment
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            description = f"{event['description']}\n\nCreated at: {timestamp}"
            description_input.fill(description)
            
            # Click save button
            save_button = self._page.wait_for_selector('button:has-text("Opslaan")', state='visible')
            if not save_button:
                self.browser_logger.error("Could not find save button")
                return False
            save_button.click()
            
            # Wait for save to complete
            try:
                self._page.wait_for_load_state('networkidle', timeout=5000)
                self.browser_logger.info("Hours added successfully")
                return True
            except TimeoutError:
                self.browser_logger.error("Save timed out")
                self.save_page_content("save_timeout")
                self._page.screenshot(path="error_save_timeout.png")
                return False
                
        except Exception as e:
            self.browser_logger.error(f"Failed to add hours: {str(e)}")
            self.save_page_content("add_hours_error")
            self._page.screenshot(path="error_add_hours.png")
            return False 