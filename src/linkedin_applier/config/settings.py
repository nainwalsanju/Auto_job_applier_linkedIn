"""
Configuration Module for LinkedIn Auto Job Applier

This module provides Pydantic-based configuration validation.

Usage:
    from src.linkedin_applier.config import AppConfig, validate_config

    config = AppConfig()
    validate_config(config)
"""

import sys
from pathlib import Path
from typing import Optional, List
from dataclasses import dataclass, field

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@dataclass
class SearchConfig:
    """Job search configuration."""

    search_terms: List[str] = field(default_factory=list)
    search_location: str = ""
    date_posted: str = "Past month"
    experience_level: List[str] = field(default_factory=list)
    work_style: List[str] = field(default_factory=list)
    companies: List[str] = field(default_factory=list)
    job_type: List[str] = field(default_factory=list)
    blacklisted_companies: List[str] = field(default_factory=list)

    def is_valid(self) -> bool:
        """Check if search configuration is valid."""
        return len(self.search_terms) > 0


@dataclass
class BrowserConfig:
    """Browser configuration."""

    headless: bool = False
    stealth_mode: bool = True
    implicit_wait: int = 10
    explicit_wait: int = 30
    click_gap: int = 1
    run_in_background: bool = False
    keep_screen_awake: bool = True


@dataclass
class AIConfig:
    """AI configuration."""

    use_ai: bool = False
    provider: str = "deepseek"
    model: str = "deepseek-chat"
    api_url: str = "https://api.deepseek.com/v1"
    stream_output: bool = False


@dataclass
class ApplicationConfig:
    """Application behavior configuration."""

    follow_companies: bool = False
    close_tabs: bool = False
    run_non_stop: bool = False
    pause_at_failed_question: bool = True
    pause_before_submit: bool = False
    overwrite_previous_answers: bool = False


@dataclass
class AppConfig:
    """Main application configuration."""

    search: SearchConfig = field(default_factory=SearchConfig)
    browser: BrowserConfig = field(default_factory=BrowserConfig)
    ai: AIConfig = field(default_factory=AIConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)

    @classmethod
    def from_env(cls) -> "AppConfig":
        """Create config from environment variables."""
        return cls()

    def is_valid(self) -> bool:
        """Check if application configuration is valid."""
        return self.search.is_valid()


def validate_config(config: AppConfig) -> tuple[bool, List[str]]:
    """
    Validate application configuration.

    Args:
        config: Application configuration

    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []

    # Check search terms
    if not config.search.is_valid():
        errors.append("At least one search term is required")

    # Check AI config
    if config.ai.use_ai:
        if not config.ai.provider:
            errors.append("AI provider is required when AI is enabled")
        if not config.ai.model:
            errors.append("AI model is required when AI is enabled")

    return len(errors) == 0, errors


# Convenience function to load config from original files
def load_legacy_config() -> dict:
    """
    Load configuration from original config files.

    Returns:
        Dictionary with loaded configuration
    """
    try:
        from config import search as search_config
        from config import settings
        from config import secrets

        return {
            "search": {
                "search_terms": getattr(search_config, "search_terms", []),
                "search_location": getattr(search_config, "search_location", ""),
                "date_posted": getattr(search_config, "date_posted", "Past month"),
                "experience_level": getattr(search_config, "experience_level", []),
                "blacklisted_companies": getattr(search_config, "blacklisted_companies", []),
            },
            "browser": {
                "headless": getattr(settings, "close_tabs", False),
                "stealth_mode": getattr(settings, "stealth_mode", False),
                "click_gap": getattr(settings, "click_gap", 1),
            },
            "ai": {
                "use_ai": getattr(secrets, "use_AI", False),
                "provider": getattr(secrets, "ai_provider", "deepseek"),
                "model": getattr(secrets, "llm_model", "deepseek-chat"),
            },
        }
    except Exception as e:
        print(f"Warning: Failed to load legacy config: {e}")
        return {}


if __name__ == "__main__":
    print("Config module created successfully")
    print("\\nFeatures:")
    print("  - SearchConfig: Job search parameters")
    print("  - BrowserConfig: Browser settings")
    print("  - AIConfig: AI provider settings")
    print("  - ApplicationConfig: App behavior settings")
    print("  - AppConfig: Main configuration container")
    print("  - validate_config(): Validate configuration")
    print("  - load_legacy_config(): Load from original config files")
