"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Navigation and login logic for Glassdoor.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from modules.helpers import print_lg, buffer
from modules.glassdoor_selectors import *


def glassdoor_login(driver, username, password):
    """Handles Glassdoor login process."""
    try:
        print_lg(f"Attempting Glassdoor login for {username}...")
        driver.get(LOGIN_URL)
        buffer(2)

        user_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, USERNAME_FIELD))
        )
        user_field.send_keys(username)

        pass_field = driver.find_element(By.XPATH, PASSWORD_FIELD)
        pass_field.send_keys(password)

        driver.find_element(By.XPATH, SUBMIT_LOGIN).click()
        buffer(5)

        # Verify login
        if "login" not in driver.current_url.lower():
            print_lg("✅ Glassdoor login successful")
            return True
        else:
            print_lg("❌ Glassdoor login failed - still on login page")
            return False

    except Exception as e:
        print_lg(f"❌ Glassdoor login error: {e}")
        return False


def glassdoor_search(driver, keywords, location):
    """Performs job search on Glassdoor."""
    try:
        print_lg(f"Searching Glassdoor for '{keywords}' in '{location}'...")
        driver.get(SEARCH_URL)
        buffer(3)

        title_input = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.XPATH, JOB_TITLE_INPUT))
        )
        title_input.clear()
        title_input.send_keys(keywords)

        loc_input = driver.find_element(By.XPATH, LOCATION_INPUT)
        loc_input.clear()
        loc_input.send_keys(location)

        driver.find_element(By.XPATH, SEARCH_BUTTON).click()
        buffer(5)

        return True
    except Exception as e:
        print_lg(f"❌ Glassdoor search error: {e}")
        return False
