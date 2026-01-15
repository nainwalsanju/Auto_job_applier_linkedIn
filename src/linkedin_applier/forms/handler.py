"""
Form Handler Module for LinkedIn Auto Job Applier

This module handles answering form questions in job applications.

Usage:
    from src.linkedin_applier.forms.handler import FormHandler

    handler = FormHandler(driver, wait)
    handler.fill_form(answers)
"""

import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import personals, questions as q_config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support.select import Select
from selenium.common.exceptions import NoSuchElementException

from ..utils.logger import log
from ..forms.parser import FormParser, FormField
from ..exceptions import QuestionAnsweringError


class FormHandler:
    """
    Handles filling out forms and answering questions.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
        parser: FormParser instance
    """

    def __init__(self, driver, wait):
        """
        Initialize the form handler.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait
        self.parser = FormParser(driver, wait)

    def fill_form(
        self, answers: Optional[Dict[str, str]] = None, ai_answerer: Optional[Callable] = None
    ) -> List[Dict[str, str]]:
        """
        Fill out the current form with answers.

        Args:
            answers: Pre-defined answers for questions
            ai_answerer: Optional function to generate AI answers

        Returns:
            List of answered questions with their answers
        """
        answers = answers or {}
        answered = []

        # Detect all fields
        fields = self.parser.detect_all_fields()

        for field in fields:
            try:
                # Check if we have a pre-defined answer
                answer = answers.get(field.label, "")

                if not answer:
                    # Try to get answer from config
                    answer = self._get_config_answer(field)

                if not answer and ai_answerer:
                    # Use AI to generate answer
                    answer = ai_answerer(field.label, field.options)
                    answered.append(
                        {"question": field.label, "answer": answer, "ai_generated": True}
                    )
                elif answer:
                    # Fill the answer
                    if self._fill_field(field, answer):
                        answered.append(
                            {"question": field.label, "answer": answer, "ai_generated": False}
                        )

                # Small delay between fields
                time.sleep(0.5)

            except Exception as e:
                log.warning(f"Failed to fill field '{field.label}': {e}")
                continue

        log.info(f"Filled {len(answered)} form fields")
        return answered

    def _get_config_answer(self, field: FormField) -> str:
        """Get answer from configuration based on field label."""
        label_lower = field.label.lower()

        # Personal info
        if any(kw in label_lower for kw in ["email", "e-mail"]):
            return getattr(personals, "email", "")

        if any(kw in label_lower for kw in ["phone", "mobile", "cell"]):
            return getattr(personals, "phone_number", "")

        if "first name" in label_lower:
            return getattr(personals, "first_name", "")

        if "last name" in label_lower:
            return getattr(personals, "last_name", "")

        if any(kw in label_lower for kw in ["full name", "name"]):
            return f"{personals.first_name} {personals.last_name}"

        # Location
        if any(kw in label_lower for kw in ["city", "town"]):
            return getattr(personals, "city", "")

        if any(kw in label_lower for kw in ["state", "province"]):
            return getattr(personals, "state", "")

        if any(kw in label_lower for kw in ["country", "nation"]):
            return getattr(personals, "country", "")

        if "address" in label_lower:
            return getattr(personals, "address", "")

        if "zip" in label_lower or "postal" in label_lower:
            return getattr(personals, "zip_code", "")

        # Experience
        if any(kw in label_lower for kw in ["years", "experience", "exp"]):
            return getattr(personals, "years_of_experience", "5")

        if "current job" in label_lower or "current title" in label_lower:
            return getattr(personals, "current_job_title", "")

        if "current company" in label_lower or "employer" in label_lower:
            return getattr(personals, "current_company", "")

        # Notice period
        if any(kw in label_lower for kw in ["notice", "joining"]):
            return getattr(personals, "notice_period_months", "1")

        # Salary
        if "salary" in label_lower and "expectation" in label_lower:
            return getattr(personals, "expected_salary", "10")

        # LinkedIn profile
        if "linkedin" in label_lower:
            return getattr(personals, "linkedin_profile_url", "")

        # Website/Portfolio
        if "portfolio" in label_lower or "website" in label_lower:
            return getattr(personals, "website", "")

        # Education
        if "degree" in label_lower:
            return getattr(personals, "highest_degree", "Bachelor's")

        if "university" in label_lower or "college" in label_lower or "school" in label_lower:
            return getattr(personals, "university", "")

        # For select fields, try to match option
        if field.field_type == "select" and field.options:
            return self._match_option(label_lower, field.options)

        return ""

    def _match_option(self, label: str, options: List[str]) -> str:
        """Match a label to the best option."""
        label_words = set(label.lower().split())

        best_match = ""
        best_score = 0

        for option in options:
            option_words = set(option.lower().split())
            score = len(label_words & option_words)
            if score > best_score:
                best_score = score
                best_match = option

        return best_match

    def _fill_field(self, field: FormField, answer: str) -> bool:
        """
        Fill a single form field.

        Args:
            field: FormField object
            answer: Answer to fill

        Returns:
            True if successful
        """
        try:
            # Find the input element
            input_elem = self._find_input_element(field)
            if not input_elem:
                return False

            # Fill based on field type
            if field.field_type == "select":
                return self._fill_select(input_elem, answer, field.options)

            elif field.field_type in ["radio", "checkbox"]:
                return self._fill_radio(field, answer)

            elif field.field_type in ["textarea", "text"]:
                return self._fill_text(input_elem, answer)

            else:
                return self._fill_text(input_elem, answer)

        except Exception as e:
            log.warning(f"Failed to fill field '{field.label}': {e}")
            return False

    def _find_input_element(self, field: FormField) -> Optional[Any]:
        """Find the input element for a field."""
        try:
            # Try to find by label association
            label_text = field.label[:30]  # Use first 30 chars

            # Various ways inputs might be associated with labels
            selectors = [
                f"//label[contains(text(), '{label_text}')]//following::input[1]",
                f"//label[contains(text(), '{label_text}')]//following::select[1]",
                f"//label[contains(text(), '{label_text}')]//following::textarea[1]",
                f"//label[contains(text(), '{label_text}')]/..//input",
                f"//*[contains(@aria-label, '{label_text}')]",
            ]

            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        element = self.driver.find_element(By.XPATH, selector)
                    else:
                        element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element
                except NoSuchElementException:
                    continue

            return None

        except Exception:
            return None

    def _fill_select(self, select_elem, answer: str, options: List[str]) -> bool:
        """Fill a select dropdown."""
        try:
            select = Select(select_elem)

            # Try to select by visible text
            try:
                select.select_by_visible_text(answer)
                return True
            except:
                pass

            # Try to find matching option
            for opt in select.options:
                if answer.lower() in opt.text.lower():
                    opt.click()
                    return True

            # Default to first option if answer not found
            if options:
                select.select_by_index(1)
                return True

            return False

        except Exception as e:
            log.warning(f"Failed to fill select: {e}")
            return False

    def _fill_radio(self, field: FormField, answer: str) -> bool:
        """Fill a radio button or checkbox."""
        try:
            # Find the option that matches the answer
            label_text = answer[:30]

            selectors = [
                f"//label[contains(text(), '{label_text}')]",
                f"//*[contains(text(), '{label_text}')]",
            ]

            for selector in selectors:
                try:
                    if selector.startswith("//"):
                        option = self.driver.find_element(By.XPATH, selector)
                    else:
                        option = self.driver.find_element(By.CSS_SELECTOR, selector)

                    option.click()
                    return True
                except NoSuchElementException:
                    continue

            return False

        except Exception as e:
            log.warning(f"Failed to fill radio: {e}")
            return False

    def _fill_text(self, input_elem, answer: str) -> bool:
        """Fill a text input or textarea."""
        try:
            input_elem.clear()
            input_elem.send_keys(answer)
            return True

        except Exception as e:
            log.warning(f"Failed to fill text: {e}")
            return False

    def answer_single_question(
        self, question: str, answer: str, question_type: str = "text"
    ) -> bool:
        """
        Answer a single question.

        Args:
            question: Question label
            answer: Answer to provide
            question_type: Type of question

        Returns:
            True if successful
        """
        field = FormField(label=question, field_type=question_type, selector="")
        return self._fill_field(field, answer)

    def get_unanswered_questions(self) -> List[FormField]:
        """Get list of unanswered required questions."""
        fields = self.parser.detect_all_fields()
        unanswered = []

        for field in fields:
            if field.required:
                # Check if field has value
                input_elem = self._find_input_element(field)
                if input_elem:
                    value = input_elem.get_attribute("value") or input_elem.text
                    if not value.strip():
                        unanswered.append(field)

        return unanswered


if __name__ == "__main__":
    print("FormHandler module created successfully")
    print("\\nFeatures:")
    print("  - fill_form(answers, ai_answerer)")
    print("  - answer_single_question(question, answer, type)")
    print("  - get_unanswered_questions()")
    print("  - _get_config_answer(field)")
