"""
Messaging Utility for LinkedIn
Standalone tool to send personalized messages to recruiters and connections.

Author: Sanjay Nainwal
"""

# Imports
import sys
import os
import time
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.secrets import username, password, ai_provider, use_AI
from config.settings import *
from config.recruiter_messaging import *
from modules.helpers import print_lg, buffer
from modules.recruiter_messenger import (
    generate_personalized_message,
    send_message_to_recruiter,
    track_sent_message,
    check_daily_message_limit,
)

# Global tracker
messages_sent_today = 0


def setup_browser():
    """
    Explicit browser setup with error handling.
    Returns (driver, wait, actions) or (None, None, None) if setup fails.
    """
    try:
        print_lg("Initializing browser for messaging utility...")
        # Import browser setup modules
        # Note: modules.open_chrome executes setup on import
        from modules.open_chrome import driver, wait, actions

        if driver is None:
            raise Exception("Driver initialization failed")

        print_lg("Browser setup successful")
        return driver, wait, actions
    except Exception as e:
        print_lg(f"Failed to setup browser: {e}")
        return None, None, None


def try_find_xp(driver, xpath, timeout=1):
    """Try to find an element by XPath with a timeout."""
    try:
        return WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.XPATH, xpath))
        )
    except:
        return None


def is_logged_in_LN(driver) -> bool:
    """Check if currently logged into LinkedIn."""
    try:
        if "linkedin.com/feed" in driver.current_url:
            return True

        # Check for common login elements
        if driver.find_elements(By.ID, "global-nav-typeahead"):
            return True

        # Check if login button is present
        if driver.find_elements(By.XPATH, "//button[contains(text(), 'Sign in')]"):
            return False

        return False
    except:
        return False


def login_with_timeout(driver, timeout=120):
    """
    Attempts automated login, then waits for manual intervention with timeout.
    """
    if is_logged_in_LN(driver):
        print_lg("Already logged in.")
        return True

    try:
        print_lg("Attempting automated login...")
        driver.get("https://www.linkedin.com/login")

        username_field = WebDriverWait(driver, 10).until(
            EC.presence_of_element_located((By.ID, "username"))
        )
        password_field = driver.find_element(By.ID, "password")

        username_field.send_keys(username)
        password_field.send_keys(password)

        login_button = driver.find_element(By.XPATH, "//button[@type='submit']")
        login_button.click()

        time.sleep(5)  # Wait for redirect

        if is_logged_in_LN(driver):
            print_lg("Automated login successful!")
            return True

    except Exception as e:
        print_lg(f"Automated login failed: {e}")

    print_lg("\n" + "=" * 50)
    print_lg("MANUAL LOGIN REQUIRED")
    print_lg(f"Please log in manually in the browser window.")
    print_lg(f"Waiting up to {timeout} seconds for login detection...")
    print_lg("=" * 50 + "\n")

    start_time = time.time()
    while time.time() - start_time < timeout:
        if is_logged_in_LN(driver):
            print_lg("Login detected! Proceeding...")
            return True

        elapsed = int(time.time() - start_time)
        if elapsed % 10 == 0:
            print_lg(f"Still waiting for login... ({elapsed}s elapsed)")

        time.sleep(2)

    print_lg("Login timeout reached. Exiting.")
    return False


def find_people_to_message(driver, search_keywords: list) -> list[dict]:
    """Find people from search results based on keywords."""
    people = []
    try:
        for keyword in search_keywords:
            print_lg(f"Searching for: {keyword}")
            search_url = (
                f"https://www.linkedin.com/search/results/people/?keywords={keyword}"
            )
            driver.get(search_url)
            time.sleep(5)  # Allow results to load

            # Find all result items
            cards = driver.find_elements(
                By.XPATH, "//li[contains(@class, 'reusable-search__result-item')]"
            )
            for card in cards[:5]:  # Limit to top 5 per keyword for safety
                try:
                    name_elem = card.find_element(
                        By.XPATH,
                        ".//span[contains(@class, 'entity-result__title-text')]//a",
                    )
                    name = name_elem.text.strip().split("\n")[0]
                    link = name_elem.get_attribute("href").split("?")[0]

                    people.append(
                        {
                            "name": name,
                            "profile_link": link,
                            "recruiter_id": link.split("/in/")[-1].strip("/"),
                        }
                    )
                    print_lg(f" Found: {name}")
                except:
                    continue
    except Exception as e:
        print_lg(f"Error searching for people: {e}")
    return people


def main():
    """Main execution entry point."""
    global messages_sent_today

    print_lg("=== LinkedIn Messaging Utility ===")

    # 1. Setup Browser
    driver, wait, actions = setup_browser()
    if not driver:
        return

    try:
        # 2. Login
        if not login_with_timeout(driver):
            return

        # 3. AI Client Setup
        ai_client = None
        if use_AI:
            try:
                print_lg(f"Initializing AI client ({ai_provider})...")
                if ai_provider.lower() == "openai":
                    from modules.ai.openaiConnections import ai_create_openai_client

                    ai_client = ai_create_openai_client()
                elif ai_provider.lower() == "deepseek":
                    from modules.ai.deepseekConnections import deepseek_create_client

                    ai_client = deepseek_create_client()
                elif ai_provider.lower() == "gemini":
                    from modules.ai.geminiConnections import gemini_create_client

                    ai_client = gemini_create_client()
            except Exception as e:
                print_lg(f"AI initialization failed: {e}")

        # 4. Search and Message
        keywords = ["Technical Recruiter", "Hiring Manager", "Engineering Lead"]
        people = find_people_to_message(driver, keywords)

        print_lg(f"Found {len(people)} potential contacts.")

        for person in people:
            if check_daily_message_limit():
                print_lg("Daily limit reached.")
                break

            print_lg(f"Processing: {person['name']}")

            # Generate message
            subject, message = generate_personalized_message(
                ai_client,
                person,
                "",
                "Networking",
                "Professional Network",
                person["profile_link"],
            )

            # Send message
            message_data = {"subject": subject, "body": message}
            success, error = send_message_to_recruiter(driver, person, message_data)

            # Track
            track_sent_message(
                "manual_utility",
                "Networking",
                "N/A",
                "N/A",
                person,
                subject,
                message,
                success,
                "",
                error,
            )

            if success:
                messages_sent_today += 1
                print_lg(f" Successfully messaged {person['name']}")
            else:
                print_lg(f" Failed to message {person['name']}: {error}")

            buffer(message_delay_seconds)

    except Exception as e:
        print_lg(f"Fatal error in main: {e}")
    finally:
        print_lg(f"Cleanup: Closing browser. Messages sent: {messages_sent_today}")
        driver.quit()


if __name__ == "__main__":
    main()
