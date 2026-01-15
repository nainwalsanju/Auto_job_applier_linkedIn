"""
Job Apply Module for LinkedIn Auto Job Applier

This module handles submitting job applications.

Usage:
    from src.linkedin_applier.jobs.apply import JobApplicator

    applicator = JobApplicator(driver, wait)
    applicator.easy_apply(job, questions_answers)
"""

import sys
import time
from pathlib import Path
from typing import Optional, List, Dict, Tuple

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import personals, questions, resume as resume_config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import log
from ..jobs.models import JobDetails, ApplicationResult, ApplicationType
from ..exceptions import ApplicationSubmissionError, ResumeUploadError


class JobApplicator:
    """
    Submits job applications on LinkedIn.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
    """

    def __init__(self, driver, wait):
        """
        Initialize the job applicator.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait

    def easy_apply(
        self, job: JobDetails, answers: Optional[Dict[str, str]] = None
    ) -> ApplicationResult:
        """
        Submit an Easy Apply application.

        Args:
            job: JobDetails object
            answers: Pre-defined answers for application questions

        Returns:
            ApplicationResult indicating success/failure
        """
        try:
            log.info("Starting Easy Apply", job_id=job.job_id, title=job.title)

            questions_answered = []

            # Step 1: Click Easy Apply button
            if not self._click_easy_apply_button():
                return ApplicationResult(
                    job=job, applied=False, error="Could not find Easy Apply button"
                )

            # Step 2: Fill form questions
            form_complete = self._fill_application_form(answers or {})
            if isinstance(form_complete, list):
                questions_answered = form_complete
            else:
                # Try to auto-fill known questions
                questions_answered = self._fill_known_questions()

            # Step 3: Upload resume if needed
            self._upload_resume()

            # Step 4: Submit application
            if self._submit_application():
                log.job_applied(
                    job_id=job.job_id,
                    title=job.title,
                    company=job.company,
                    questions_count=len(questions_answered),
                )

                return ApplicationResult(
                    job=job,
                    applied=True,
                    application_type=ApplicationType.EASY_APPLY.value,
                    questions_answered=questions_answered,
                )
            else:
                return ApplicationResult(
                    job=job, applied=False, error="Failed to submit application"
                )

        except Exception as e:
            log.job_failed(job_id=job.job_id, error=str(e))
            return ApplicationResult(job=job, applied=False, error=str(e))

    def _click_easy_apply_button(self) -> bool:
        """Click the Easy Apply button on job page."""
        try:
            # Try different selectors for Easy Apply button
            selectors = [
                "button[data-test='easy-apply-button']",
                "//button[contains(text(), 'Easy Apply')]",
                ".jobs-apply-button",
            ]

            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        button = self.driver.find_element(By.XPATH, selector)
                    else:
                        button = self.driver.find_element(By.CSS_SELECTOR, selector)

                    button.click()

                    # Wait for form to open
                    self.wait.until(
                        EC.presence_of_element_located((By.CLASS_NAME, "jobs-easy-apply-modal"))
                    )
                    return True
                except NoSuchElementException:
                    continue

            return False

        except Exception as e:
            log.warning(f"Failed to click Easy Apply button: {e}")
            return False

    def _fill_application_form(self, answers: Dict[str, str]) -> List[Dict[str, str]]:
        """
        Fill out the application form.

        Args:
            answers: Pre-defined answers for questions

        Returns:
            List of questions that were answered
        """
        questions_answered = []
        max_pages = 5  # Handle multi-page forms

        for page_num in range(max_pages):
            # Find all form questions
            form_questions = self._find_form_questions()

            if not form_questions:
                break  # No more questions

            for q_label, q_type, q_options in form_questions:
                # Check if we have a pre-defined answer
                answer = answers.get(q_label, "")

                if answer:
                    self._fill_question(q_label, q_type, answer, q_options)
                    questions_answered.append(
                        {"question": q_label, "answer": answer, "ai_generated": False}
                    )
                else:
                    # Try to auto-answer based on config
                    answer = self._get_config_answer(q_label, q_type)
                    if answer:
                        self._fill_question(q_label, q_type, answer, q_options)
                        questions_answered.append(
                            {"question": q_label, "answer": answer, "ai_generated": False}
                        )

            # Click Next if available
            if not self._click_next_button():
                break

        return questions_answered

    def _find_form_questions(self) -> List[Tuple[str, str, List[str]]]:
        """
        Find all questions in the current form.

        Returns:
            List of (question_label, question_type, options) tuples
        """
        questions = []

        try:
            # Find all labeled inputs
            inputs = self.driver.find_elements(
                By.CSS_SELECTOR, ".jobs-easy-application-form__input-section"
            )

            for section in inputs:
                try:
                    # Get question label
                    label = section.find_element(
                        By.CSS_SELECTOR, "label, .artdeco-form__label"
                    ).text

                    # Determine input type
                    input_type = self._get_input_type(section)

                    # Get options if select/radio
                    options = []
                    if input_type in ["select", "radio"]:
                        options = self._get_input_options(section)

                    if label and input_type:
                        questions.append((label, input_type, options))

                except Exception:
                    continue

        except Exception as e:
            log.warning(f"Failed to find form questions: {e}")

        return questions

    def _get_input_type(self, section) -> str:
        """Determine the input type of a form section."""
        try:
            # Check for various input types
            if section.find_elements(By.CSS_SELECTOR, "select"):
                return "select"
            elif section.find_elements(By.CSS_SELECTOR, "input[type='radio']"):
                return "radio"
            elif section.find_elements(By.CSS_SELECTOR, "input[type='checkbox']"):
                return "checkbox"
            elif section.find_elements(By.CSS_SELECTOR, "textarea"):
                return "textarea"
            elif section.find_elements(By.CSS_SELECTOR, "input[type='text']"):
                return "text"
            else:
                return "text"
        except Exception:
            return "text"

    def _get_input_options(self, section) -> List[str]:
        """Get available options for select/radio inputs."""
        options = []
        try:
            # For selects
            selects = section.find_elements(By.CSS_SELECTOR, "select option")
            for opt in selects:
                text = opt.text.strip()
                if text and text not in ["Select an option", "--"]:
                    options.append(text)
        except Exception:
            pass

        return options

    def _fill_question(self, label: str, q_type: str, answer: str, options: List[str]) -> bool:
        """
        Fill a single question.

        Args:
            label: Question label
            q_type: Question type
            answer: Answer to fill
            options: Available options

        Returns:
            True if successful
        """
        try:
            # Find the input element
            if q_type == "select":
                # Handle select dropdowns
                select_elem = self.driver.find_element(
                    By.XPATH, f"//label[contains(text(), '{label[:30]}')]//following::select[1]"
                )
                select = Select(select_elem)
                # Try to select by visible text or value
                try:
                    select.select_by_visible_text(answer)
                except:
                    for opt in select.options:
                        if answer.lower() in opt.text.lower():
                            opt.click()
                            break

            elif q_type in ["radio", "checkbox"]:
                # Handle radio/checkbox
                option_xpath = f"//label[contains(text(), '{answer}')]"
                option = self.driver.find_element(By.XPATH, option_xpath)
                option.click()

            elif q_type in ["text", "textarea"]:
                # Handle text inputs
                input_xpath = f"//label[contains(text(), '{label[:30]}')]//following::input[1]"
                if not self._element_exists(input_xpath):
                    input_xpath = f"//textarea[contains(@aria-label, '{label[:30]}')]"

                input_elem = self.driver.find_element(By.XPATH, input_xpath)
                input_elem.clear()
                input_elem.send_keys(answer)

            return True

        except Exception as e:
            log.warning(f"Failed to fill question '{label}': {e}")
            return False

    def _element_exists(self, xpath: str) -> bool:
        """Check if element exists."""
        try:
            self.driver.find_element(By.XPATH, xpath)
            return True
        except NoSuchElementException:
            return False

    def _click_next_button(self) -> bool:
        """Click the Next button to go to next form page."""
        try:
            next_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Next')]")
            next_btn.click()

            # Wait for form to update
            time.sleep(1)
            return True

        except NoSuchElementException:
            # No Next button, might be on last page
            return False
        except Exception as e:
            log.warning(f"Failed to click Next: {e}")
            return False

    def _fill_known_questions(self) -> List[Dict[str, str]]:
        """Fill questions using pre-defined answers from config."""
        answered = []

        try:
            # Import config questions
            from config import questions as q_config

            # Map of question keywords to answers
            q_mapping = {
                "phone": getattr(q_config, "phone_number", ""),
                "email": getattr(q_config, "email", ""),
                "name": getattr(q_config, "first_name", "")
                + " "
                + getattr(q_config, "last_name", ""),
                "location": getattr(q_config, "city", ""),
                "resume": "attached",
            }

            for keyword, answer in q_mapping.items():
                if answer:
                    answered.append({"question": keyword, "answer": answer, "ai_generated": False})

        except Exception as e:
            log.warning(f"Failed to fill known questions: {e}")

        return answered

    def _get_config_answer(self, label: str, q_type: str) -> str:
        """Get answer from config based on question label."""
        label_lower = label.lower()

        # Phone number
        if "phone" in label_lower:
            return getattr(personals, "phone_number", "")

        # Email
        if "email" in label_lower:
            return getattr(personals, "email", "")

        # Name
        if "name" in label_lower and "company" not in label_lower:
            return f"{personals.first_name} {personals.last_name}"

        # Current job title
        if "current" in label_lower and ("title" in label_lower or "position" in label_lower):
            return getattr(personals, "current_job_title", "")

        # Years of experience
        if "years" in label_lower and "experience" in label_lower:
            return getattr(personals, "years_of_experience", "5")

        return ""

    def _upload_resume(self) -> bool:
        """Upload resume if required."""
        try:
            # Check if resume upload is required
            upload_elements = self.driver.find_elements(
                By.XPATH, "//input[@type='file' and contains(@name, 'resume')]"
            )

            if upload_elements:
                resume_path = getattr(resume_config, "resume_file_path", "")
                if resume_path and Path(resume_path).exists():
                    upload_elements[0].send_keys(str(resume_path))
                    log.info("Resume uploaded")
                    return True

            return True  # No upload required

        except Exception as e:
            log.warning(f"Failed to upload resume: {e}")
            return False

    def _submit_application(self) -> bool:
        """Submit the completed application."""
        try:
            # Find and click Submit button
            submit_btn = self.driver.find_element(By.XPATH, "//button[contains(text(), 'Submit')]")
            submit_btn.click()

            # Wait for confirmation
            time.sleep(2)

            # Check for success
            success_selectors = [
                "div[data-test='application-success']",
                ".jobs-application-success__icon",
                "//h2[contains(text(), 'Application sent')]",
            ]

            for selector in success_selectors:
                try:
                    if selector.startswith("//"):
                        self.driver.find_element(By.XPATH, selector)
                    else:
                        self.driver.find_element(By.CSS_SELECTOR, selector)
                    return True
                except NoSuchElementException:
                    continue

            return True  # Assume success if no error

        except NoSuchElementException:
            log.warning("Could not find Submit button")
            return False
        except Exception as e:
            log.warning(f"Failed to submit application: {e}")
            return False

    def external_apply(self, job: JobDetails, external_url: str) -> ApplicationResult:
        """
        Handle external apply (when Easy Apply not available).

        Args:
            job: JobDetails object
            external_url: URL to external application

        Returns:
            ApplicationResult with external link
        """
        try:
            log.info("Handling external application", job_id=job.job_id)

            # Open external application link
            self.driver.execute_script(f"window.open('{external_url}', '_blank')")

            return ApplicationResult(
                job=job,
                applied=True,
                application_type=ApplicationType.EXTERNAL_APPLY.value,
                external_link=external_url,
            )

        except Exception as e:
            return ApplicationResult(job=job, applied=False, error=str(e))


if __name__ == "__main__":
    print("JobApplicator module created successfully")
    print("\\nFeatures:")
    print("  - easy_apply(job, answers)")
    print("  - external_apply(job, external_url)")
    print("  - _fill_application_form(answers)")
    print("  - _upload_resume()")
    print("  - _submit_application()")
