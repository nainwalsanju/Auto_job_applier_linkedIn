"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Orchesrator for Glassdoor job applications.
"""

import sys
import os
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from modules.helpers import print_lg, buffer, make_directories, session_stats
from modules.open_chrome import open_chrome
from modules.bot_logger import init_session_logger, log_step, finalize_session
from modules.notifications import notify_job_applied, notify_session_summary
from config.glassdoor_config import *
from modules.glassdoor_navigator import glassdoor_login, glassdoor_search
from modules.glassdoor_selectors import (
    JOB_LIST_ITEMS,
    JOB_TITLE_LINK,
    APPLY_BUTTON,
    GD_EASY_APPLY_INDICATOR,
)
from modules.glassdoor_applier import fill_glassdoor_application
import modules.resume_tailor as resume_tailor


def run_glassdoor_bot():
    """Main entry point for Glassdoor automation."""
    driver = None
    try:
        # 1. Initialize
        init_session_logger()
        log_step("Initializing Glassdoor Bot")

        driver, wait = open_chrome()

        # 2. Login
        if not glassdoor_login(driver, glassdoor_username, glassdoor_password):
            print_lg("Failed to login to Glassdoor. Check your credentials in .env")
            return

        # 3. Search Loop
        for keyword in glassdoor_keywords:
            log_step(f"Starting search for: {keyword}")
            if not glassdoor_search(driver, keyword, glassdoor_location):
                continue

            # 4. Iterate Jobs
            buffer(3)
            job_listings = driver.find_elements(By.XPATH, JOB_LIST_ITEMS)
            print_lg(f"Found {len(job_listings)} job listings on current page.")

            for index, job in enumerate(job_listings[:max_glassdoor_apps_per_run]):
                try:
                    # Click job to load details
                    job.click()
                    buffer(2)

                    # Check if it's Easy Apply
                    try:
                        easy_apply_badge = job.find_element(
                            By.XPATH, GD_EASY_APPLY_INDICATOR
                        )
                        print_lg(f"Job {index + 1}: Easy Apply detected.")
                    except:
                        print_lg(f"Job {index + 1}: Not an Easy Apply job, skipping.")
                        continue

                    # Get basic info for notifications
                    title = job.find_element(By.XPATH, JOB_TITLE_LINK).text
                    print_lg(f"Processing: {title}")

                    # NEW: Get Job Description for context
                    description = ""
                    try:
                        description_elem = driver.find_element(
                            By.XPATH, "//div[@id='JobDescriptionContainer']"
                        )
                        description = description_elem.text
                    except:
                        pass

                    # NEW: Tailor Resume for Glassdoor
                    job_details = {
                        "title": title,
                        "company": "Glassdoor Employer",  # Extracted later
                        "description": description,
                        "location": glassdoor_location,
                    }

                    # Trigger apply
                    success, msg = fill_glassdoor_application(driver, wait, job_details)

                    if success:
                        session_stats["jobs_processed"] += 1
                        notify_job_applied(title, "Glassdoor", "Glassdoor Bot", False)

                except Exception as e:
                    print_lg(f"Error processing job {index}: {e}")
                    continue

    except Exception as e:
        print_lg(f"🛑 Critical Glassdoor Bot Error: {e}")
    finally:
        log_step("Finalizing Glassdoor Session")
        finalize_session(session_stats)
        notify_session_summary(session_stats)
        if driver:
            driver.quit()


if __name__ == "__main__":
    run_glassdoor_bot()
