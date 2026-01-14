"""
Custom Exception Hierarchy for LinkedIn Auto Job Applier

This module provides a comprehensive exception hierarchy for better error handling
and debugging. All custom exceptions inherit from LinkedInApplierError.

Example:
    try:
        result = apply_to_job(driver, job)
    except ApplicationError as e:
        logger.error(f"Application failed: {e.message}")
        save_failed_application(e)
"""

from typing import Optional, Any


class LinkedInApplierError(Exception):
    """
    Base exception for all LinkedIn Applier errors.

    Attributes:
        message: Human-readable error message
        details: Additional context about the error
        code: Error code for programmatic handling
    """

    def __init__(
        self,
        message: str,
        details: Optional[dict[str, Any]] = None,
        code: Optional[str] = None,
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.code = code

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to dictionary for logging/serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "code": self.code,
            "details": self.details,
        }


class BrowserError(LinkedInApplierError):
    """Base exception for browser-related errors."""

    pass


class BrowserInitializationError(BrowserError):
    """
    Raised when browser initialization fails.

    Causes:
        - Missing Chrome/ChromeDriver
        - Invalid profile path
        - Extension conflicts
    """

    pass


class BrowserNavigationError(BrowserError):
    """
    Raised when navigation to a URL fails.

    Causes:
        - Network issues
        - Invalid URL
        - Page load timeout
    """

    pass


class ElementNotFoundError(BrowserError):
    """
    Raised when an expected element is not found on the page.

    Causes:
        - Page structure changed
        - Element is in shadow DOM
        - Element requires interaction to appear
    """

    def __init__(
        self,
        message: str,
        selector: Optional[str] = None,
        timeout: Optional[float] = None,
        **kwargs,
    ):
        details = kwargs.pop("details", {})
        if selector:
            details["selector"] = selector
        if timeout:
            details["timeout"] = timeout
        super().__init__(message, details=details, **kwargs)


class ElementInteractionError(BrowserError):
    """
    Raised when interaction with an element fails.

    Causes:
        - Element is not interactable
        - Element is covered by another
        - Element is disabled
    """

    pass


class SessionError(LinkedInApplierError):
    """Base exception for session-related errors."""

    pass


class NotLoggedInError(SessionError):
    """Raised when user is not logged in to LinkedIn."""

    pass


class SessionExpiredError(SessionError):
    """Raised when LinkedIn session expires during operation."""

    pass


class ApplicationError(LinkedInApplierError):
    """Base exception for job application errors."""

    pass


class ApplicationSubmissionError(ApplicationError):
    """
    Raised when job application submission fails.

    Causes:
        - Form validation errors
        - Required fields missing
        - Network issues during submission
    """

    pass


class QuestionAnsweringError(ApplicationError):
    """
    Raised when AI fails to answer a form question.

    Causes:
        - Unknown question type
        - AI API failure
        - Invalid response format
    """

    pass


class ResumeUploadError(ApplicationError):
    """
    Raised when resume upload fails.

    Causes:
        - Invalid file format
        - File too large
        - Upload timeout
    """

    pass


class AIError(LinkedInApplierError):
    """Base exception for AI-related errors."""

    pass


class AIConnectionError(AIError):
    """
    Raised when connection to AI provider fails.

    Causes:
        - Invalid API key
        - Network issues
        - Rate limiting
    """

    pass


class AIResponseError(AIError):
    """
    Raised when AI returns an invalid or unexpected response.

    Causes:
        - Malformed JSON
        - Unexpected response format
        - Content policy violation
    """

    pass


class AIQuotaExceededError(AIError):
    """Raised when AI API quota is exceeded."""

    pass


class ConfigurationError(LinkedInApplierError):
    """Base exception for configuration errors."""

    pass


class MissingConfigurationError(ConfigurationError):
    """
    Raised when required configuration is missing.

    Causes:
        - Environment variables not set
        - Missing .env file
        - Required config keys absent
    """

    pass


class InvalidConfigurationError(ConfigurationError):
    """
    Raised when configuration value is invalid.

    Causes:
        - Type mismatch
        - Value out of range
        - Invalid format
    """

    pass


class JobFilterError(LinkedInApplierError):
    """Base exception for job filtering errors."""

    pass


class BlacklistMatchError(JobFilterError):
    """
    Raised when a job matches blacklist criteria.

    This is not an error but a filter decision - jobs should be skipped.
    """

    pass


class JobParseError(LinkedInApplierError):
    """
    Raised when job data cannot be parsed correctly.

    Causes:
        - Page structure changed
        - Missing required fields
        - Malformed data
    """

    pass


class RateLimitError(LinkedInApplierError):
    """
    Raised when rate limiting is triggered.

    Causes:
        - Too many applications
        - LinkedIn anti-bot measures
        - API rate limits
    """

    pass


class HumanVerificationError(LinkedInApplierError):
    """
    Raised when LinkedIn requires human verification.

    Causes:
        - Suspicious activity
        - CAPTCHA required
        - Phone verification
    """

    pass
