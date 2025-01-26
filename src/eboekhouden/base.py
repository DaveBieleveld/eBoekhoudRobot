"""Base class for e-boekhouden client."""

import os
import logging
from typing import Optional
from playwright.sync_api import ElementHandle
from src.config import config

class EBoekhoudenBase:
    """Base class with common utility methods."""
    
    def save_page_content(self, name: str, frame: Optional[ElementHandle] = None):
        """Save the page or frame content to a file for debugging."""
        if self.browser_logger.getEffectiveLevel() <= logging.DEBUG:
            try:
                content = frame.content() if frame else self._page.content()
                with open(os.path.join("temp", f"{name}.html"), "w", encoding="utf-8") as f:
                    f.write(content)
            except Exception as e:
                self.browser_logger.warning(f"Could not save page content for {name}: {str(e)}")

    def take_screenshot(self, name: str):
        """Take a screenshot and save it in the temp/screenshots directory."""
        screenshot_path = os.path.join(config.directories.screenshots_dir, f"{name}.png")
        self._page.screenshot(path=screenshot_path) 