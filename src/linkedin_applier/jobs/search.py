"""
Job Search Module for LinkedIn Auto Job Applier

This module handles LinkedIn job searching and navigation.

Usage:
    from src.linkedin_applier.jobs.search import JobSearcher

    searcher = JobSearcher(driver, wait)
    searcher.search("Python Developer", "Remote")
"""

import sys
from pathlib import Path
from typing import Optional, List
from datetime import datetime

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import search as search_config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import log
from ..jobs.models import JobDetails
from ..exceptions import BrowserNavigationError, JobParseError


class JobSearcher:
    """
    Handles LinkedIn job searching and result navigation.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        current_page: Current page number in search results
        current_term: Current search term
    """

    def __init__(self, driver, wait):
        """
        Initialize the job searcher.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait
        self.current_page = 1
        self.current_term = ""
        self.current_location = ""

    def search(self, search_term: str, location: str = "", url_filters: str = "") -> None:
        """
        Navigate to job search results page.

        Args:
            search_term: Job title or keywords
            location: Location to search in
            url_filters: URL filters (e.g., "&f_E=2")

        Raises:
            BrowserNavigationError: If navigation fails
        """
        try:
            log.info("Searching for jobs", term=search_term, location=location)

            # Build search URL
            base_url = "https://www.linkedin.com/jobs/search/"
            params = f"?keywords={search_term.replace(' ', '%20')}"

            if location:
                params += f"&location={location.replace(' ', '%20')}"

            if url_filters:
                params += url_filters

            full_url = base_url + params

            self.driver.get(full_url)
            self.current_term = search_term
            self.current_location = location

            # Wait for results to load
            self.wait.until(EC.presence_of_element_located((By.CLASS_NAME, "jobs-search-results")))

            log.info("Job search results loaded", url=full_url)

        except Exception as e:
            raise BrowserNavigationError(
                f"Failed to search for jobs: {str(e)}",
                details={"search_term": search_term, "location": location},
            )

    def navigate_to_page(self, page_number: int) -> bool:
        """
        Navigate to a specific page of search results.

        Args:
            page_number: Page number to navigate to

        Returns:
            True if navigation successful, False if no more pages
        """
        try:
            log.info("Navigating to page", page=page_number)

            # Click on page number or "Next" button
            page_selector = f"//button[@aria-label='Page {page_number}']"

            try:
                page_btn = self.driver.find_element(By.XPATH, page_selector)
                page_btn.click()
                self.current_page = page_number

                # Wait for results to update
                self.wait.until(
                    EC.staleness_of(
                        self.driver.find_element(By.CLASS_NAME, "jobs-search-results-list")
                    )
                )
                return True

            except NoSuchElementException:
                log.info("No more pages available")
                return False

        except Exception as e:
            log.warning(f"Failed to navigate to page {page_number}: {e}")
            return False

    def get_job_cards(self) -> List:
        """
        Get list of job card elements from current page.

        Returns:
            List of job card WebElements
        """
        try:
            # LinkedIn's job card selector
            job_cards = self.driver.find_elements(By.CSS_SELECTOR, ".jobs-search-results__list li")
            return job_cards
        except Exception as e:
            log.warning(f"Failed to get job cards: {e}")
            return []

    def get_total_results(self) -> int:
        """
        Get total number of search results.

        Returns:
            Total count of jobs found
        """
        try:
            results_text = self.driver.find_element(
                By.CSS_SELECTOR, ".jobs-search-results__subtitle"
            ).text

            # Extract number from text like "12,345 results"
            import re

            numbers = re.findall(r"[\d,]+", results_text)
            if numbers:
                return int(numbers[0].replace(",", ""))
            return 0
        except Exception:
            return 0

    def has_next_page(self) -> bool:
        """
        Check if there are more pages of results.

        Returns:
            True if next page exists
        """
        try:
            # Check for pagination or results count
            job_cards = self.get_job_cards()
            return len(job_cards) > 0
        except Exception:
            return False

    def scroll_results(self, scroll_count: int = 3) -> None:
        """
        Scroll through job results to load more.

        Args:
            scroll_count: Number of times to scroll
        """
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.keys import Keys

        try:
            for _ in range(scroll_count):
                # Scroll down
                self.driver.find_element(By.TAG_NAME, "body").send_keys(Keys.END)
                import time

                time.sleep(1)

        except Exception as e:
            log.warning(f"Failed to scroll results: {e}")

    def click_job(self, job_card) -> bool:
        """
        Click on a job card to view details.

        Args:
            job_card: Job card WebElement

        Returns:
            True if click successful
        """
        try:
            job_card.click()

            # Wait for details panel to load
            self.wait.until(
                EC.presence_of_element_located((By.CLASS_NAME, "jobs-details__container"))
            )
            return True
        except Exception as e:
            log.warning(f"Failed to click job: {e}")
            return False


if __name__ == "__main__":
    print("JobSearcher module created successfully")
    print("\\nFeatures:")
    print("  - search(term, location, filters)")
    print("  - navigate_to_page(page_number)")
    print("  - get_job_cards()")
    print("  - get_total_results()")
    print("  - has_next_page()")
    print("  - scroll_results()")
    print("  - click_job()")
