"""
Job Parser Module for LinkedIn Auto Job Applier

This module extracts and parses job details from LinkedIn.

Usage:
    from src.linkedin_applier.jobs.parser import JobParser

    parser = JobParser(driver, wait)
    job = parser.parse_job_details()
    skills = parser.extract_skills(job.description)
"""

import sys
import re
from pathlib import Path
from typing import Optional, List, Dict, Tuple
from datetime import datetime

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import search as search_config
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import TimeoutException, NoSuchElementException

from ..utils.logger import log
from ..jobs.models import JobDetails
from ..exceptions import JobParseError


class JobParser:
    """
    Parses job details from LinkedIn job postings.

    Attributes:
        driver: Selenium WebDriver instance
        wait: WebDriverWait instance
    """

    # Common skill patterns for extraction
    SKILL_PATTERNS = [
        r"\bPython\b",
        r"\bJavaScript\b",
        r"\bTypeScript\b",
        r"\bJava\b",
        r"\bC\+\+\b",
        r"\bC#\b",
        r"\bGo\b",
        r"\bRust\b",
        r"\bSQL\b",
        r"\bReact\b",
        r"\bAngular\b",
        r"\bVue\b",
        r"\bNode\.?js\b",
        r"\bDjango\b",
        r"\bFlask\b",
        r"\bSpring\b",
        r"\bAWS\b",
        r"\bAzure\b",
        r"\bGCP\b",
        r"\bDocker\b",
        r"\bKubernetes\b",
        r"\bGit\b",
        r"\bLinux\b",
        r"\bREST\b",
        r"\bAPI\b",
        r"\bMachine Learning\b",
        r"\bML\b",
        r"\bAI\b",
        r"\bNLP\b",
        r"\bTensorFlow\b",
        r"\bPyTorch\b",
    ]

    # Experience patterns
    EXPERIENCE_PATTERNS = [
        r"(\d+)\+?\s*years?\s*(?:of\s*)?(?:experience|exp)",
        r"(\d+)\s*-\s*\d+\s*years?",
        r"minimum\s*(\d+)\s*years?",
        r"at\s*least\s*(\d+)\s*years?",
    ]

    # Bad words for job filtering
    BAD_WORDS = [
        "senior",
        "sr",
        "sr.",
        "junior",
        "jr",
        "jr.",
        "intern",
        "contract",
        "freelance",
        "part-time",
        "part time",
        "unpaid",
        "volunteer",
    ]

    def __init__(self, driver, wait):
        """
        Initialize the job parser.

        Args:
            driver: Selenium WebDriver instance
            wait: WebDriverWait instance
        """
        self.driver = driver
        self.wait = wait

    def parse_job_details(self, job_id: Optional[str] = None) -> JobDetails:
        """
        Parse all job details from the current job posting.

        Args:
            job_id: Job ID if known, will be extracted if not provided

        Returns:
            JobDetails object with all parsed information

        Raises:
            JobParseError: If parsing fails
        """
        try:
            log.info("Parsing job details")

            # Extract job ID
            if not job_id:
                job_id = self._extract_job_id()

            # Extract title
            title = self._extract_title()

            # Extract company
            company = self._extract_company()

            # Extract location
            location = self._extract_location()

            # Extract work style (remote/hybrid)
            work_style = self._extract_work_style()

            # Extract description
            description = self._extract_description()

            # Extract skills
            skills = self.extract_skills(description)

            # Extract experience required
            experience = self.extract_experience(description)

            # Check for blacklist keywords
            skip, skip_reason = self.check_blacklist(description, company)

            # Check for security clearance requirement
            requires_clearance = self._check_security_clearance(description)

            # Check for repost
            reposted = self._check_reposted()

            job = JobDetails(
                job_id=job_id,
                title=title,
                company=company,
                work_location=location,
                work_style=work_style,
                description=description,
                experience_required=experience,
                skills=skills,
                reposted=reposted,
            )

            if skip:
                job.skills = []  # Mark as skipped

            log.info(
                "Job parsed successfully",
                job_id=job_id,
                title=title,
                company=company,
                skills_count=len(skills),
            )

            return job

        except Exception as e:
            raise JobParseError(f"Failed to parse job details: {str(e)}")

    def _extract_job_id(self) -> str:
        """Extract job ID from page URL or element."""
        try:
            # Try to get from URL
            current_url = self.driver.current_url
            if "jobs/view/" in current_url:
                # Extract ID from URL like .../jobs/view/123456789/...
                parts = current_url.split("/jobs/view/")
                if len(parts) > 1:
                    job_id_part = parts[1].split("?")[0]
                    return job_id_part

            # Fallback to element
            job_id = self.driver.find_element(By.CSS_SELECTOR, "[data-job-id]").get_attribute(
                "data-job-id"
            )

            return job_id or "unknown"

        except Exception:
            return "unknown"

    def _extract_title(self) -> str:
        """Extract job title."""
        try:
            title = self.driver.find_element(
                By.CSS_SELECTOR, ".job-details__main-content h1, h1[data-test='job-details-title']"
            ).text
            return title.strip()
        except Exception:
            return "Unknown"

    def _extract_company(self) -> str:
        """Extract company name."""
        try:
            company = self.driver.find_element(
                By.CSS_SELECTOR,
                ".job-details__company-name, [data-test='job-details-company-name']",
            ).text
            return company.strip()
        except Exception:
            return "Unknown"

    def _extract_location(self) -> str:
        """Extract job location."""
        try:
            location = self.driver.find_element(
                By.CSS_SELECTOR, ".job-details__location, [data-test='job-details-location']"
            ).text
            return location.strip()
        except Exception:
            return "Unknown"

    def _extract_work_style(self) -> str:
        """Extract work style (remote, hybrid, on-site)."""
        try:
            # Check for remote/hybrid indicators
            description = self._extract_description().lower()

            if "remote" in description or "work from home" in description:
                return "Remote"
            elif "hybrid" in description:
                return "Hybrid"
            else:
                return "On-site"

        except Exception:
            return "Unknown"

    def _extract_description(self) -> str:
        """Extract full job description."""
        try:
            # Try different selectors
            selectors = [
                ".job-details__description-content",
                "[data-test='job-details-description']",
                ".description__text",
                ".jobs-description__content",
            ]

            for selector in selectors:
                try:
                    element = self.driver.find_element(By.CSS_SELECTOR, selector)
                    return element.text
                except NoSuchElementException:
                    continue

            return ""

        except Exception:
            return ""

    def extract_skills(self, description: str) -> List[str]:
        """
        Extract skills from job description.

        Args:
            description: Job description text

        Returns:
            List of extracted skills
        """
        skills = set()
        description_lower = description.lower()

        for pattern in self.SKILL_PATTERNS:
            matches = re.findall(pattern, description, re.IGNORECASE)
            for match in matches:
                skills.add(match.strip())

        # Filter out very short matches
        skills = [s for s in skills if len(s) > 1]

        return list(skills)

    def extract_experience(self, description: str) -> Optional[int]:
        """
        Extract years of experience required from description.

        Args:
            description: Job description text

        Returns:
            Years of experience required, or None if not found
        """
        description_lower = description.lower()

        for pattern in self.EXPERIENCE_PATTERNS:
            match = re.search(pattern, description_lower, re.IGNORECASE)
            if match:
                years = int(match.group(1))
                return years

        return None

    def check_blacklist(self, description: str, company: str) -> Tuple[bool, str]:
        """
        Check if job should be skipped due to blacklist.

        Args:
            description: Job description
            company: Company name

        Returns:
            Tuple of (should_skip, reason)
        """
        # Check company blacklist
        if hasattr(search_config, "blacklisted_companies"):
            for bad_company in search_config.blacklisted_companies:
                if bad_company.lower() in company.lower():
                    return True, f"Company '{company}' is blacklisted"

        # Check for bad words in title
        title = self._extract_title().lower()
        for word in self.BAD_WORDS:
            if word in title:
                return True, f"Found bad word in title: '{word}'"

        return False, ""

    def _check_security_clearance(self, description: str) -> bool:
        """Check if job requires security clearance."""
        clearance_keywords = [
            "security clearance required",
            "must have security clearance",
            "active security clearance",
            "us citizenship required",
            "clearance required",
        ]

        description_lower = description.lower()
        for keyword in clearance_keywords:
            if keyword in description_lower:
                return True

        return False

    def _check_reposted(self) -> bool:
        """Check if job is a repost."""
        try:
            repost_elements = self.driver.find_elements(
                By.XPATH, "//*[contains(text(), 'reposted')]"
            )
            return len(repost_elements) > 0
        except Exception:
            return False

    def extract_about_company(self) -> Optional[str]:
        """Extract about company section if available."""
        try:
            # Look for "About the company" section
            about_section = self.driver.find_element(
                By.XPATH, "//h3[contains(text(), 'About the company')]"
            )
            parent = about_section.find_element(By.XPATH, "..")
            return parent.text
        except Exception:
            return None


if __name__ == "__main__":
    print("JobParser module created successfully")
    print("\\nFeatures:")
    print("  - parse_job_details()")
    print("  - extract_skills(description)")
    print("  - extract_experience(description)")
    print("  - check_blacklist(description, company)")
    print("  - extract_about_company()")
