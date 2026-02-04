"""
Author:     Sanjay Nainwal
GitHub:     https://github.com/nainwalsanju/Auto_job_applier_linkedIn
Description: Logic for filling out Glassdoor's "Easy Apply" forms.
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from modules.helpers import print_lg, buffer
from modules.glassdoor_selectors import (
    FORM_CONTAINER,
    CONTINUE_BUTTON,
    SUBMIT_APP_BUTTON,
)
from modules.optimized_answer_questions import answer_questions


def fill_glassdoor_application(driver, wait, job_details):
    """
    Handles the multi-step form for Glassdoor Easy Apply.
    """
    try:
        print_lg(f"Opening application form for {job_details['title']}...")

        # Click the primary apply button to open modal
        from modules.glassdoor_selectors import APPLY_BUTTON

        driver.find_element(By.XPATH, APPLY_BUTTON).click()

        # 1. Wait for form to appear
        form = wait.until(EC.presence_of_element_located((By.XPATH, FORM_CONTAINER)))

        # 2. Step through the form
        steps_processed = 0
        max_steps = 10

        while steps_processed < max_steps:
            steps_processed += 1
            buffer(2)

            # RESUME UPLOAD (Typically on one of the first steps)
            try:
                resume_input = driver.find_element(By.XPATH, "//input[@type='file']")
                if resume_input:
                    from config.questions import default_resume_path

                    resume_input.send_keys(os.path.abspath(default_resume_path))
                    print_lg("📤 Uploaded resume to Glassdoor form.")
                    buffer(1)
            except:
                pass

            # Check for Submit button (Final Step)

            try:
                submit_btn = driver.find_element(By.XPATH, SUBMIT_APP_BUTTON)
                if submit_btn.is_displayed():
                    print_lg("🚀 Submit button found. Finalizing application...")
                    # submit_btn.click() # Gated for safety during initial dev
                    return True, "Form ready for submission"
            except NoSuchElementException:
                pass

            # Handle standard questions (reusing AI logic)
            # Note: We pass the form container as the 'modal' to the existing answer_questions logic
            print_lg(f"Step {steps_processed}: Answering questions...")
            try:
                # This assumes glassdoor forms use similar input patterns as LinkedIn (common in web apps)
                answer_questions(
                    driver,
                    set(),
                    job_details.get("location", ""),
                    job_details.get("description", ""),
                )
            except Exception as e:
                print_lg(f"⚠️ Non-critical error answering questions: {e}")

            # Click Continue/Next
            try:
                continue_btn = driver.find_element(By.XPATH, CONTINUE_BUTTON)
                if continue_btn.is_displayed():
                    continue_btn.click()
                    print_lg(f"Step {steps_processed}: Clicked Continue")
                else:
                    break
            except NoSuchElementException:
                print_lg("Reached end of form steps or no continue button found.")
                break

        return False, "Could not reach submit step"

    except Exception as e:
        print_lg(f"❌ Failed to fill Glassdoor application: {e}")
        return False, str(e)
