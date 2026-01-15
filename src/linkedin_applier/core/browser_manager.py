"""
Browser Manager for LinkedIn Auto Job Applier

This module handles browser initialization, configuration, and lifecycle management.
Uses undetected-chromedriver for stealth mode.
"""

import os
import sys
from pathlib import Path
from typing import Optional

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings


class BrowserManager:
    """
    Manages browser lifecycle for LinkedIn automation.

    Attributes:
        headless: Run browser in headless mode
        stealth_mode: Use undetected-chromedriver for stealth
        driver: The Selenium WebDriver instance
        wait: WebDriverWait instance
    """

    def __init__(
        self,
        headless: bool = False,
        stealth_mode: bool = False,
        user_data_dir: Optional[str] = None,
        profile_dir: Optional[str] = None,
    ):
        """
        Initialize the browser manager.

        Args:
            headless: Run without GUI
            stealth_mode: Use anti-detection measures
            user_data_dir: Chrome user data directory
            profile_dir: Chrome profile directory
        """
        self.headless = headless
        self.stealth_mode = stealth_mode
        self.user_data_dir = user_data_dir
        self.profile_dir = profile_dir
        self.driver = None
        self.wait = None
        self.actions = None
        self._initialized = False

    def initialize(self):
        """
        Initialize the browser and WebDriver.

        Raises:
            BrowserInitializationError: If browser fails to initialize
        """
        if self._initialized:
            return

        try:
            try:
                import undetected_chromedriver as uc

                use_stealth = True
            except ImportError:
                print("undetected-chromedriver not available, falling back to regular Chrome")
                from selenium import webdriver

                uc = None
                use_stealth = False

            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.action_chains import ActionChains

            print(
                f"Initializing browser... headless={self.headless}, stealth={self.stealth_mode}, use_stealth_driver={use_stealth}"
            )

            # Configure Chrome options - use minimal, compatible options
            if use_stealth:
                options = uc.ChromeOptions()
            else:
                from selenium.webdriver.chrome.options import Options

                options = Options()

            # Basic options only - avoid problematic ones
            if self.headless:
                options.add_argument("--headless")

            # Essential options for stability
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--window-size=1920,1080")

            # User data and profile (only if specified)
            if self.user_data_dir:
                options.add_argument(f"--user-data-dir={self.user_data_dir}")
            if self.profile_dir:
                options.add_argument(f"--profile-directory={self.profile_dir}")

            # Minimal stealth options - avoid aggressive ones that cause crashes
            if self.stealth_mode and use_stealth:
                # Very basic stealth - remove automation indicators
                options.add_argument("--disable-blink-features=AutomationControlled")
                # Remove the webdriver property
                options.add_experimental_option("useAutomationExtension", False)

            # Initialize driver with better error handling
            if use_stealth:
                try:
                    # Try with automatic version detection first
                    self.driver = uc.Chrome(options=options)
                except Exception as e:
                    print(f"Failed with automatic version detection: {e}")
                    # Fallback to manual version detection
                    try:
                        self.driver = uc.Chrome(options=options, version_main=None)
                    except Exception as e2:
                        print(f"Failed with manual version detection: {e2}")
                        # Last resort: try without version specification
                        try:
                            # Create options without problematic settings
                            simple_options = uc.ChromeOptions()
                            simple_options.add_argument("--no-sandbox")
                            simple_options.add_argument("--disable-dev-shm-usage")
                            if self.headless:
                                simple_options.add_argument("--headless")
                            simple_options.add_argument("--window-size=1920,1080")
                            self.driver = uc.Chrome(options=simple_options)
                            print("Browser initialized with minimal options")
                        except Exception as e3:
                            print(f"All browser initialization attempts failed: {e3}")
                            raise
            else:
                # Use regular selenium webdriver
                try:
                    from selenium.webdriver.chrome.service import Service
                    from webdriver_manager.chrome import ChromeDriverManager

                    # Try to use webdriver-manager for automatic chromedriver management
                    try:
                        service = Service(ChromeDriverManager().install())
                        self.driver = webdriver.Chrome(service=service, options=options)
                        print("Browser initialized with webdriver-manager")
                    except ImportError:
                        # webdriver-manager not available, try direct path
                        self.driver = webdriver.Chrome(options=options)
                        print("Browser initialized with direct chromedriver")
                except Exception as e:
                    print(f"Regular Chrome driver failed: {e}")
                    # Try with minimal options
                    try:
                        minimal_options = Options()
                        minimal_options.add_argument("--no-sandbox")
                        minimal_options.add_argument("--disable-dev-shm-usage")
                        if self.headless:
                            minimal_options.add_argument("--headless")
                        minimal_options.add_argument("--window-size=1920,1080")
                        self.driver = webdriver.Chrome(options=minimal_options)
                        print("Browser initialized with minimal options (regular driver)")
                    except Exception as e2:
                        print(f"All driver initialization attempts failed: {e2}")
                        raise

            # Set implicit wait (default 10 seconds)
            implicit_wait = getattr(settings, "implicit_wait", 10)
            self.driver.implicitly_wait(implicit_wait)

            # Create explicit wait (default 30 seconds)
            explicit_wait = getattr(settings, "explicit_wait", 30)
            self.wait = WebDriverWait(self.driver, explicit_wait)

            # Create actions chain
            self.actions = ActionChains(self.driver)

            # Remove webdriver property for stealth
            if self.stealth_mode:
                self.driver.execute_script(
                    "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
                )

            self._initialized = True
            print("Browser initialized successfully")

        except ImportError:
            print("Note: undetected-chromedriver not installed. Browser functionality limited.")
            self._initialized = True
        except Exception as e:
            print(f"Failed to initialize browser: {e}")
            raise

    def get_driver(self):
        """Get the WebDriver instance."""
        return self.driver

    def close(self) -> None:
        """Close the browser and cleanup resources."""
        if self.driver:
            print("Closing browser...")
            try:
                self.driver.quit()
            except Exception as e:
                print(f"Error closing browser: {e}")
            finally:
                self.driver = None
                self._initialized = False

    def __enter__(self):
        """Context manager entry."""
        self.initialize()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()
        return False


def create_browser(headless: bool = False, stealth_mode: bool = False) -> BrowserManager:
    """
    Factory function to create a configured browser manager.

    Args:
        headless: Run without GUI
        stealth_mode: Use anti-detection measures

    Returns:
        Configured BrowserManager instance
    """
    manager = BrowserManager(headless=headless, stealth_mode=stealth_mode)
    manager.initialize()
    return manager


if __name__ == "__main__":
    print("Testing BrowserManager...")

    try:
        manager = BrowserManager(headless=True, stealth_mode=True)
        manager.initialize()
        print("BrowserManager initialized successfully")
        manager.close()
        print("Browser closed successfully")
    except Exception as e:
        print(f"Note: Browser initialization failed (expected without GUI): {e}")
