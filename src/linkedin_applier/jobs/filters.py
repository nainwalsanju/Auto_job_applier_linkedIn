"""
Job Filters Module for LinkedIn Auto Job Applier

This module handles applying search filters to job results.

Usage:
    from src.linkedin_applier.jobs.filters import JobFilter

    filters = JobFilter(driver, wait)
    filters.set_date_filter("Past week")
    filters.set_location("Remote")
"""

import sys
from pathlib import Path
from typing import Optional, List

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import log


class JobFilter:
    """
    Applies and manages job search filters.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
    """

    def __init__(self, driver, wait):
        """
        Initialize the job filter.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait

    def set_date_filter(self, filter_option: str) -> bool:
        """
        Set date posted filter.

        Args:
            filter_option: "Past 24 hours", "Past week", "Past month", etc.

        Returns:
            True if successful
        """
        try:
            log.info("Setting date filter", filter=filter_option)

            # Click on date filter button
            date_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Date posted')]"
            )
            date_btn.click()

            # Select the option
            option_xpath = f"//label[contains(text(), '{filter_option}')]"
            option = self.driver.find_element(By.XPATH, option_xpath)
            option.click()

            # Apply the filter
            apply_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show results')]"
            )
            apply_btn.click()

            log.info("Date filter applied", filter=filter_option)
            return True

        except Exception as e:
            log.warning(f"Failed to set date filter: {e}")
            return False

    def set_location_filter(self, location: str) -> bool:
        """
        Set location filter.

        Args:
            location: City, country, or "Remote"

        Returns:
            True if successful
        """
        try:
            log.info("Setting location filter", location=location)

            # Click on location filter
            location_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Location')]"
            )
            location_btn.click()

            # Enter location
            input_field = self.driver.find_element(
                By.XPATH, "//input[@placeholder='Search location']"
            )
            input_field.clear()
            input_field.send_keys(location)

            # Select first result
            first_result = self.driver.find_element(
                By.CSS_SELECTOR, ".search-typeahead__option:first-child"
            )
            first_result.click()

            # Apply
            apply_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show results')]"
            )
            apply_btn.click()

            log.info("Location filter applied", location=location)
            return True

        except Exception as e:
            log.warning(f"Failed to set location filter: {e}")
            return False

    def set_experience_filter(self, levels: List[str]) -> bool:
        """
        Set experience level filter.

        Args:
            levels: List like ["Mid-Senior", "Entry level"]

        Returns:
            True if successful
        """
        try:
            log.info("Setting experience filter", levels=levels)

            # Click experience filter
            exp_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Experience level')]"
            )
            exp_btn.click()

            # Select each level
            for level in levels:
                option_xpath = f"//label[contains(text(), '{level}')]"
                try:
                    option = self.driver.find_element(By.XPATH, option_xpath)
                    option.click()
                except NoSuchElementException:
                    log.warning(f"Experience level not found: {level}")

            # Apply
            apply_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show results')]"
            )
            apply_btn.click()

            log.info("Experience filter applied", levels=levels)
            return True

        except Exception as e:
            log.warning(f"Failed to set experience filter: {e}")
            return False

    def set_work_style_filter(self, work_styles: List[str]) -> bool:
        """
        Set work style filter (Remote, Hybrid, On-site).

        Args:
            work_styles: List like ["Remote", "Hybrid"]

        Returns:
            True if successful
        """
        try:
            log.info("Setting work style filter", styles=work_styles)

            # Click work style filter
            style_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Work style')]"
            )
            style_btn.click()

            # Select each style
            for style in work_styles:
                option_xpath = f"//label[contains(text(), '{style}')]"
                try:
                    option = self.driver.find_element(By.XPATH, option_xpath)
                    option.click()
                except NoSuchElementException:
                    log.warning(f"Work style not found: {style}")

            # Apply
            apply_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show results')]"
            )
            apply_btn.click()

            log.info("Work style filter applied", styles=work_styles)
            return True

        except Exception as e:
            log.warning(f"Failed to set work style filter: {e}")
            return False

    def set_company_filter(self, companies: List[str]) -> bool:
        """
        Set company filter.

        Args:
            companies: List of company names

        Returns:
            True if successful
        """
        try:
            log.info("Setting company filter", companies=companies)

            # Click company filter
            company_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Company')]"
            )
            company_btn.click()

            for company in companies:
                # Enter company name
                input_field = self.driver.find_element(
                    By.XPATH, "//input[@placeholder='Search companies']"
                )
                input_field.clear()
                input_field.send_keys(company)

                # Select first result
                try:
                    first_result = self.driver.find_element(
                        By.CSS_SELECTOR, ".search-typeahead__option:first-child"
                    )
                    first_result.click()
                except NoSuchElementException:
                    log.warning(f"Company not found: {company}")

            # Apply
            apply_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Show results')]"
            )
            apply_btn.click()

            log.info("Company filter applied", companies=companies)
            return True

        except Exception as e:
            log.warning(f"Failed to set company filter: {e}")
            return False

    def clear_all_filters(self) -> bool:
        """
        Clear all applied filters.

        Returns:
            True if successful
        """
        try:
            # Click clear all
            clear_btn = self.driver.find_element(
                By.XPATH, "//button[contains(text(), 'Clear all')]"
            )
            clear_btn.click()

            log.info("All filters cleared")
            return True

        except Exception as e:
            log.warning(f"Failed to clear filters: {e}")
            return False

    def apply_config_filters(self) -> bool:
        """
        Apply filters from configuration.

        Uses filters defined in config/search.py

        Returns:
            True if all filters applied successfully
        """
        try:
            from config import search as search_config

            success = True

            # Apply date filter
            if hasattr(search_config, "date_posted") and search_config.date_posted:
                if not self.set_date_filter(search_config.date_posted):
                    success = False

            # Apply experience filter
            if hasattr(search_config, "experience_level") and search_config.experience_level:
                if not self.set_experience_filter(search_config.experience_level):
                    success = False

            # Apply work style filter
            if hasattr(search_config, "work_style") and search_config.work_style:
                if not self.set_work_style_filter(search_config.work_style):
                    success = False

            # Apply company filter
            if hasattr(search_config, "companies") and search_config.companies:
                if not self.set_company_filter(search_config.companies):
                    success = False

            return success

        except Exception as e:
            log.warning(f"Failed to apply config filters: {e}")
            return False


if __name__ == "__main__":
    print("JobFilter module created successfully")
    print("\\nFeatures:")
    print("  - set_date_filter(option)")
    print("  - set_location_filter(location)")
    print("  - set_experience_filter(levels)")
    print("  - set_work_style_filter(styles)")
    print("  - set_company_filter(companies)")
    print("  - clear_all_filters()")
    print("  - apply_config_filters()")
