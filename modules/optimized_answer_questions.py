"""
Optimized Answer Questions Module for LinkedIn Auto Job Applier

This module provides high-performance form answering for LinkedIn Easy Apply.
Improvements:
- Single-pass element detection (CSS selectors)
- Zero artificial delays (removed sleep calls)
- Expanded pre-defined answer patterns
- Intelligent AI fallback
- Answer caching per session
"""

import time
from typing import Set, Dict, Any, Tuple
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.select import Select
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException, TimeoutException


class OptimizedAnswerer:
    def __init__(self, config_dict: Dict[str, Any]):
        self.config = config_dict
        self.cached_answers = {}  # Label -> Answer
        self.randomly_answered = set()

    def answer_questions(
        self,
        modal: WebElement,
        questions_list: Set,
        work_location: str,
        job_description: str = "",
    ) -> Set:
        """Main entry point for answering questions in a modal page."""

        # Find all form elements in one go
        # [data-test-form-element] is the container for each question
        all_question_containers = modal.find_elements(
            By.XPATH, ".//div[@data-test-form-element]"
        )

        for container in all_question_containers:
            try:
                # Detect question type and label
                input_elem, q_type, label_text = self._parse_question(container)
                if not input_elem or not label_text:
                    continue

                label_lower = label_text.lower()

                # Check cache first
                if label_text in self.cached_answers and not self.config.get(
                    "overwrite_previous_answers", False
                ):
                    self._fill_field(
                        input_elem, q_type, self.cached_answers[label_text]
                    )
                    questions_list.add(
                        (label_text, self.cached_answers[label_text], q_type, "Cached")
                    )
                    continue

                # 1. Try common questions logic
                answer = self._get_common_answer(label_lower, q_type, work_location)

                # 2. If no answer, try AI
                if not answer and self.config.get("use_AI"):
                    answer = self._get_ai_answer(label_text, q_type, job_description)

                # 3. Fallback to default/random if still no answer
                if not answer:
                    answer = self._get_fallback_answer(label_lower, q_type)
                    self.randomly_answered.add((label_text, q_type))

                # Fill the field
                if answer:
                    success = self._fill_field(input_elem, q_type, answer)
                    if success:
                        self.cached_answers[label_text] = answer
                        questions_list.add((label_text, answer, q_type, "New"))
            except Exception as e:
                print(f"[OptimizedAnswerer] Error answering question: {e}")
                continue

        return questions_list

    def _parse_question(self, container: WebElement) -> Tuple[WebElement, str, str]:
        """Identifies element, type, and label text."""
        # Try to find the input element
        # Priority: select > radio > textarea > text input > checkbox

        # Check for select
        selects = container.find_elements(By.TAG_NAME, "select")
        if selects:
            label = self._get_label(container)
            return selects[0], "select", label

        # Check for radio (usually inside a fieldset)
        radios = container.find_elements(
            By.XPATH,
            ".//fieldset[@data-test-form-builder-radio-button-form-component='true']",
        )
        if radios:
            label = self._get_label(container, is_fieldset=True)
            return radios[0], "radio", label

        # Check for textarea
        textareas = container.find_elements(By.TAG_NAME, "textarea")
        if textareas:
            label = self._get_label(container)
            return textareas[0], "textarea", label

        # Check for text input
        inputs = container.find_elements(By.TAG_NAME, "input")
        for inp in inputs:
            i_type = inp.get_attribute("type")
            if i_type == "text":
                label = self._get_label(container)
                return inp, "text", label
            if i_type == "checkbox":
                label = self._get_label(container)
                return inp, "checkbox", label

        return None, "", ""

    def _get_label(self, container: WebElement, is_fieldset: bool = False) -> str:
        """Extracts the question text."""
        try:
            if is_fieldset:
                legend = container.find_element(By.TAG_NAME, "legend")
                # Try to find the title span
                title = legend.find_element(
                    By.XPATH,
                    ".//span[@data-test-form-builder-radio-button-form-component__title]",
                )
                return title.text.strip()
            else:
                label = container.find_element(By.TAG_NAME, "label")
                # Handle visually hidden spans
                try:
                    return label.find_element(
                        By.XPATH, ".//span[not(contains(@class, 'visually-hidden'))]"
                    ).text.strip()
                except:
                    return label.text.strip()
        except:
            return "Unknown Question"

    def _fill_field(self, elem: WebElement, q_type: str, answer: Any) -> bool:
        """Performs the actual interaction."""
        try:
            if q_type == "select":
                s = Select(elem)
                # Try direct match
                try:
                    s.select_by_visible_text(answer)
                except:
                    # Fuzzy match
                    for opt in s.options:
                        if (
                            answer.lower() in opt.text.lower()
                            or opt.text.lower() in answer.lower()
                        ):
                            s.select_by_visible_text(opt.text)
                            return True
                    return False
            elif q_type == "radio":
                # answer is the text of the label to click
                labels = elem.find_elements(By.TAG_NAME, "label")
                for label in labels:
                    if answer.lower() in label.text.lower():
                        label.click()
                        return True
                # Fallback to first option if Yes/No not found but requested
                if labels:
                    labels[0].click()
                    return True
            elif q_type in ["text", "textarea"]:
                elem.clear()
                elem.send_keys(answer)
                # Trigger change events if needed (Enter or Tab)
                # elem.send_keys(Keys.TAB)
            elif q_type == "checkbox":
                if (answer is True or answer == "Yes") and not elem.is_selected():
                    elem.click()
                elif (answer is False or answer == "No") and elem.is_selected():
                    elem.click()
            return True
        except Exception as e:
            print(f"[OptimizedAnswerer] Fill failed for {q_type}: {e}")
            return False

    def _get_common_answer(self, label: str, q_type: str, work_location: str) -> Any:
        """Expanded local logic for common questions."""
        # Work Auth / Visa
        if any(
            x in label
            for x in ["sponsorship", "visa", "work authorization", "authorized to work"]
        ):
            return self.config.get("require_visa", "No")

        # Experience
        if any(
            x in label
            for x in ["years of experience", "how many years", "experience in"]
        ):
            return self.config.get("years_of_experience", "3")

        # Location / Relocation
        if "relocate" in label:
            return "No"
        if "remote" in label:
            return "Yes"
        if any(x in label for x in ["city", "location", "address"]):
            return self.config.get("current_city", work_location)

        # Personal info
        if "phone" in label:
            return self.config.get("phone_number", "")
        if "website" in label or "portfolio" in label:
            return self.config.get("website", "")
        if "linkedin" in label:
            return self.config.get("linkedIn", "")

        # Gender/Race/Veteran (Standard "Decline" or config)
        if any(x in label for x in ["gender", "sex"]):
            return self.config.get("gender", "Male")
        if any(x in label for x in ["race", "ethnicity"]):
            return "Decline"
        if "veteran" in label:
            return self.config.get("veteran_status", "No")
        if "disability" in label:
            return self.config.get("disability_status", "No")

        # Salary
        if any(x in label for x in ["salary", "compensation", "expectation"]):
            return self.config.get("desired_salary", "100000")

        return None

    def _get_ai_answer(self, label: str, q_type: str, job_description: str) -> str:
        """Delegates to AI client."""
        # This will be implemented by passing the AI functions in config
        ai_func = self.config.get("ai_answer_func")
        if ai_func:
            try:
                return ai_func(label, q_type, job_description)
            except:
                return ""
        return ""

    def _get_fallback_answer(self, label: str, q_type: str) -> Any:
        """Final fallback to keep the bot moving."""
        if q_type == "select":
            return "Yes"
        if q_type == "radio":
            return "Yes"
        if q_type == "checkbox":
            return True
        if q_type == "text":
            return self.config.get("years_of_experience", "3")
        if q_type == "textarea":
            return "I have extensive experience in this field."
        return ""
