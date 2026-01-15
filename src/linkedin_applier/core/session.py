"""
Session Manager for LinkedIn Auto Job Applier

This module handles LinkedIn session management - login, logout, and session validation.
"""

import sys
from pathlib import Path
from typing import Optional

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import settings, secrets
from ..exceptions import NotLoggedInError, SessionExpiredError
from ..utils.logger import log


class SessionManager:
    """
    Manages LinkedIn session state and authentication.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        is_logged_in: Current login status
    """

    def __init__(self, driver, wait):
        """
        Initialize the session manager.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait

    def is_logged_in(self) -> bool:
        """
        Check if user is logged in to LinkedIn.

        Returns:
            True if logged in, False otherwise
        """
        current_url = self.driver.current_url

        # Check for feed URL (logged in)
        if current_url == "https://www.linkedin.com/feed/":
            return True

        # Check for login page elements (not logged in)
        from selenium.webdriver.common.by import By

        if self._try_find_element(By.LINK_TEXT, "Sign in"):
            return False
        if self._try_find_element(
            By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]'
        ):
            return False
        if self._try_find_element(By.LINK_TEXT, "Join now"):
            return False

        log.warning("Could not determine login status, assuming logged in")
        return True

    def _try_find_element(self, by, value) -> bool:
        """Try to find an element, return True if found."""
        try:
            self.driver.find_element(by, value)
            return True
        except Exception:
            return False

    def login(
        self,
        username: Optional[str] = None,
        password: Optional[str] = None,
        manual_login: bool = False,
    ) -> bool:
        """
        Login to LinkedIn.

        Args:
            username: LinkedIn username (from config if not provided)
            password: LinkedIn password (from config if not provided)
            manual_login: If True, ask user to login manually

        Returns:
            True if login successful

        Raises:
            NotLoggedInError: If login fails
        """
        from selenium.webdriver.common.by import By
        from ..modules.helpers import text_input_by_ID

        # Get credentials from config if not provided
        if username is None:
            username = secrets.username
        if password is None:
            password = secrets.password

        log.info("Attempting LinkedIn login...")

        if manual_login:
            self.driver.get("https://www.linkedin.com/login")
            log.info("Please login manually. Waiting for feed URL...")

            # Wait for feed URL or user confirmation
            try:
                self.wait.until(lambda d: d.current_url == "https://www.linkedin.com/feed/")
                log.info("Manual login successful!")
                return True
            except Exception:
                raise NotLoggedInError(
                    "Manual login not completed",
                    details={
                        "recommendation": "Please login manually and ensure URL is https://www.linkedin.com/feed/"
                    },
                )

        # Try automatic login
        self.driver.get("https://www.linkedin.com/login")

        try:
            # Wait for page to load
            self.wait.until(lambda d: d.find_element(By.LINK_TEXT, "Forgot password?"))

            # Fill username
            try:
                text_input_by_ID(self.driver, "username", username, 1)
            except Exception as e:
                log.warning(f"Couldn't find username field: {e}")

            # Fill password
            try:
                text_input_by_ID(self.driver, "password", password, 1)
            except Exception as e:
                log.warning(f"Couldn't find password field: {e}")

            # Click sign in button
            sign_in_button = self.driver.find_element(
                By.XPATH, '//button[@type="submit" and contains(text(), "Sign in")]'
            )
            sign_in_button.click()

            # Wait for successful redirect
            self.wait.until(lambda d: d.current_url == "https://www.linkedin.com/feed/")

            log.info("Login successful!")
            return True

        except Exception as e:
            log.error(f"Login failed: {e}")
            raise NotLoggedInError(
                f"Failed to login: {str(e)}",
                details={"username": username[:5] + "..." if username else None},
            )

    def logout(self) -> None:
        """Logout from LinkedIn."""
        log.info("Logging out...")
        try:
            self.driver.get("https://www.linkedin.com/logout")
        except Exception as e:
            log.warning(f"Logout warning: {e}")

    def ensure_logged_in(self) -> bool:
        """
        Ensure user is logged in, login if necessary.

        Returns:
            True if logged in

        Raises:
            NotLoggedInError: If login fails
        """
        if not self.is_logged_in():
            log.info("Not logged in, attempting login...")
            return self.login()
        return True


if __name__ == "__main__":
    print("Testing SessionManager...")

    # This requires a browser to be initialized
    print("✓ SessionManager module created successfully")
    print("  - is_logged_in()")
    print("  - login(username, password)")
    print("  - logout()")
    print("  - ensure_logged_in()")
