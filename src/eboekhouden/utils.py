"""Utility functions for e-boekhouden client."""

import os
import logging
from typing import Optional
from playwright.sync_api import ElementHandle, Page
from src.config import config
from datetime import datetime, timedelta

class EBoekhoudenUtils:
    """Utility methods for EBoekhoudenClient."""

    def cleanup_debug_files(self):
        """Remove debug files older than 1 day."""
        self.browser_logger.info("Cleaning up old debug files...")
        
        debug_dir = "debug"
        if not os.path.exists(debug_dir):
            return
            
        now = datetime.now()
        cutoff = now - timedelta(days=1)
        
        for filename in os.listdir(debug_dir):
            filepath = os.path.join(debug_dir, filename)
            try:
                mtime = datetime.fromtimestamp(os.path.getmtime(filepath))
                if mtime < cutoff:
                    os.remove(filepath)
                    self.browser_logger.info(f"Removed old debug file: {filename}")
            except Exception as e:
                self.browser_logger.error(f"Error removing debug file {filename}: {str(e)}")

    def save_page_content(self, name: str) -> None:
        """Save the current page content to a file."""
        try:
            # Create debug directory if it doesn't exist
            os.makedirs("debug", exist_ok=True)
            
            # Save main page content
            content = self._page.content()
            filepath = os.path.join("debug", f"{name}.html")
            with open(filepath, "w", encoding="utf-8") as f:
                f.write(content)
            self.browser_logger.info(f"Saved page content to {filepath}")
            
            # Try to save frame contents
            for i, frame in enumerate(self._page.frames):
                try:
                    frame_content = frame.content()
                    frame_url = frame.url
                    frame_name = f"{name}_frame_{i}"
                    if "login" in frame_url.lower():
                        frame_name = f"{name}_login_frame"
                    elif "main" in frame_url.lower():
                        frame_name = f"{name}_main_frame"
                    
                    with open(f"debug/{frame_name}.html", "w", encoding="utf-8") as f:
                        f.write(f"<!-- Frame URL: {frame_url} -->\n")
                        f.write(frame_content)
                    self.browser_logger.info(f"Saved frame content to debug/{frame_name}.html")
                except Exception as e:
                    self.browser_logger.warning(f"Could not save frame {i} content: {str(e)}")
                    
        except Exception as e:
            self.browser_logger.error(f"Error saving page content: {str(e)}")

    def take_screenshot(self, name: str) -> None:
        """Take a screenshot of the current page."""
        try:
            # Create debug directory if it doesn't exist
            os.makedirs("debug", exist_ok=True)
            
            filepath = os.path.join("debug", f"{name}.png")
            self._page.screenshot(path=filepath)
            self.browser_logger.info(f"Saved screenshot to {filepath}")
            
        except Exception as e:
            self.browser_logger.error(f"Error taking screenshot: {str(e)}")

    def wait_for_table(self, selector: str, timeout: int = 5000) -> bool:
        """Wait for a table element to be visible."""
        try:
            self._page.wait_for_selector(selector, state="visible", timeout=timeout)
            return True
        except Exception as e:
            self.browser_logger.error(f"Error waiting for table: {str(e)}")
            return False 