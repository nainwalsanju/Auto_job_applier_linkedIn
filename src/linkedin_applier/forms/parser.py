"""
Form Parser Module for LinkedIn Auto Job Applier

This module detects and parses form fields in job applications.

Usage:
    from src.linkedin_applier.forms.parser import FormParser

    parser = FormParser(driver, wait)
    fields = parser.detect_all_fields()
"""

import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException

from ..utils.logger import log


class FormField:
    """Represents a single form field."""

    def __init__(
        self,
        label: str,
        field_type: str,
        selector: str,
        options: Optional[List[str]] = None,
        required: bool = False,
        placeholder: Optional[str] = None,
    ):
        self.label = label
        self.field_type = field_type  # text, textarea, select, radio, checkbox
        self.selector = selector
        self.options = options or []
        self.required = required
        self.placeholder = placeholder

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "label": self.label,
            "type": self.field_type,
            "required": self.required,
            "options_count": len(self.options),
            "placeholder": self.placeholder,
        }


class FormParser:
    """
    Detects and parses form fields in job applications.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
    """

    # Field type mappings
    FIELD_TYPE_MAP = {
        "text": "text",
        "email": "text",
        "phone": "text",
        "number": "text",
        "textarea": "textarea",
        "select": "select",
        "select-one": "select",
        "checkbox": "checkbox",
        "radio": "radio",
        "file": "file",
    }

    # Keywords for auto-detection
    LABEL_KEYWORDS = {
        "email": ["email", "e-mail", "mail"],
        "phone": ["phone", "mobile", "cell", "telephone"],
        "name": ["name", "first name", "last name", "full name"],
        "location": ["location", "address", "city", "country", "residence"],
        "resume": ["resume", "cv", "curriculum"],
        "linkedin": ["linkedin", "profile url"],
        "website": ["website", "portfolio", "personal site"],
        "years": ["years", "experience", "exp"],
        "notice": ["notice period", "notice"],
        "current": ["current", "present", "employer", "company"],
        "education": ["education", "degree", "school", "university"],
    }

    def __init__(self, driver, wait):
        """
        Initialize the form parser.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait

    def detect_all_fields(self) -> List[FormField]:
        """
        Detect all form fields on the current page.

        Returns:
            List of FormField objects
        """
        fields = []

        # Find all form sections
        sections = self._find_form_sections()

        for section in sections:
            field = self._parse_section(section)
            if field:
                fields.append(field)

        log.info(f"Detected {len(fields)} form fields")
        return fields

    def _find_form_sections(self) -> List:
        """Find all form sections/inputs."""
        try:
            # Look for form input containers
            selectors = [
                ".jobs-easy-application-form__input-section",
                ".artdeco-form__input-wrapper",
                ".fb-form__field",
                "form .input-container",
                "[data-test*='form-field']",
            ]

            for selector in selectors:
                try:
                    elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                    if elements:
                        return elements
                except Exception:
                    continue

            return []

        except Exception as e:
            log.warning(f"Failed to find form sections: {e}")
            return []

    def _parse_section(self, section) -> Optional[FormField]:
        """Parse a single form section."""
        try:
            # Try to find label
            label = self._find_label(section)
            if not label:
                return None

            # Find input element
            input_elem, input_type = self._find_input(section)
            if not input_elem:
                return None

            # Determine field type
            field_type = self.FIELD_TYPE_MAP.get(input_type or "", "text")

            # Get options if applicable
            options = []
            if field_type == "select":
                options = self._get_select_options(input_elem)
            elif field_type in ["radio", "checkbox"]:
                options = self._get_radio_options(section)

            # Check if required
            required = self._is_required(section, label)

            # Get placeholder
            placeholder = input_elem.get_attribute("placeholder") or ""

            return FormField(
                label=label,
                field_type=field_type,
                selector=self._get_selector(input_elem),
                options=options,
                required=required,
                placeholder=placeholder,
            )

        except Exception as e:
            log.debug(f"Failed to parse section: {e}")
            return None

    def _find_label(self, section) -> Optional[str]:
        """Find the label text for a form section."""
        try:
            # Try different label selectors
            selectors = [
                "label",
                ".artdeco-form__label",
                ".fb-form__label",
                ".input-label",
                "[data-test-label]",
            ]

            for selector in selectors:
                try:
                    label_elem = section.find_element(By.CSS_SELECTOR, selector)
                    text = label_elem.text.strip()
                    if text:
                        return text
                except NoSuchElementException:
                    continue

            # Try aria-label
            try:
                aria_label = section.get_attribute("aria-label") or ""
                if aria_label:
                    return aria_label.strip()
            except Exception:
                pass

            return None

        except Exception:
            return None

    def _find_input(self, section):
        """Find input element and its type."""
        try:
            # Check for different input types
            input_types = [
                ("select", ["select"]),
                ("textarea", ["textarea"]),
                ("checkbox", ["input[type='checkbox']"]),
                ("radio", ["input[type='radio']"]),
                ("file", ["input[type='file']"]),
                (
                    "text",
                    [
                        "input[type='text']",
                        "input[type='email']",
                        "input[type='tel']",
                        "input[type='url']",
                    ],
                ),
            ]

            for type_name, selectors in input_types:
                for selector in selectors:
                    try:
                        element = section.find_element(By.CSS_SELECTOR, selector)
                        return element, type_name
                    except NoSuchElementException:
                        continue

            return None, None

        except Exception:
            return None, None

    def _get_select_options(self, select_elem) -> List[str]:
        """Get options from a select element."""
        try:
            from selenium.webdriver.support.select import Select

            select = Select(select_elem)
            options = []

            for opt in select.options:
                text = opt.text.strip()
                if text and text not in ["Select an option", "--"]:
                    options.append(text)

            return options

        except Exception:
            return []

    def _get_radio_options(self, section) -> List[str]:
        """Get options for radio/checkbox groups."""
        try:
            options = []
            radios = section.find_elements(
                By.CSS_SELECTOR, "input[type='radio'], input[type='checkbox']"
            )

            for radio in radios:
                # Get associated label
                try:
                    label_id = radio.get_attribute("id")
                    if label_id:
                        label = self.driver.find_element(
                            By.CSS_SELECTOR, f"label[for='{label_id}']"
                        )
                        text = label.text.strip()
                        if text:
                            options.append(text)
                except NoSuchElementException:
                    pass

            return options

        except Exception:
            return []

    def _is_required(self, section, label: str) -> bool:
        """Check if field is required."""
        try:
            # Check for required attribute
            required_indicators = ["*", "(required)", "Required", "mandatory"]

            # Check label
            label_lower = label.lower()
            for indicator in required_indicators:
                if indicator.lower() in label_lower:
                    return True

            # Check for required attribute on input
            try:
                input_elem = section.find_element(By.CSS_SELECTOR, "input, select, textarea")
                required = input_elem.get_attribute("required")
                if required:
                    return True
            except NoSuchElementException:
                pass

            return False

        except Exception:
            return False

    def _get_selector(self, element) -> str:
        """Generate a unique selector for an element."""
        try:
            elem_id = element.get_attribute("id")
            if elem_id:
                return f"#{elem_id}"

            elem_name = element.get_attribute("name")
            if elem_name:
                return f"[name='{elem_name}']"

            # Fallback to CSS path
            return element.tag_name

        except Exception:
            return ""

    def detect_by_keywords(self) -> Dict[str, str]:
        """
        Detect fields by common keywords.

        Returns:
            Dictionary mapping field types to detected values
        """
        detected = {}
        fields = self.detect_all_fields()

        for field in fields:
            label_lower = field.label.lower()

            for keyword_type, keywords in self.LABEL_KEYWORDS.items():
                for keyword in keywords:
                    if keyword in label_lower:
                        detected[keyword_type] = field.label
                        break

        return detected


if __name__ == "__main__":
    print("FormParser module created successfully")
    print("\\nFeatures:")
    print("  - detect_all_fields()")
    print("  - detect_by_keywords()")
    print("  - FormField class")
