"""
Author:     Sai Vignesh Golla
LinkedIn:   https://www.linkedin.com/in/saivigneshgolla/

Copyright (C) 2024 Sai Vignesh Golla

License:    GNU Affero General Public License
            https://www.gnu.org/licenses/agpl-3.0.en.html

GitHub:     https://github.com/GodsScion/Auto_job_applier_linkedIn

version:    25.01.15.01.00
"""

"""
Secure Configuration Module

This module provides secure configuration management using environment variables.
Credentials are loaded from environment variables or .env files, not hardcoded.

Usage:
    from config.secure_config import get_config, get_secrets

    config = get_config()
    username = config.LINKEDIN_USERNAME
    api_key = config.LLM_API_KEY
"""

import os
from pathlib import Path
from typing import Optional
from dataclasses import dataclass, field
from functools import lru_cache


@dataclass
class AIConfig:
    """AI-related configuration."""

    use_AI: bool = False
    ai_provider: str = "deepseek"
    llm_api_url: str = "https://api.deepseek.com/v1"
    llm_api_key: str = ""
    llm_model: str = "deepseek-chat"
    llm_spec: str = "openai"
    stream_output: bool = False

    @property
    def is_configured(self) -> bool:
        """Check if AI is properly configured."""
        if not self.use_AI:
            return True
        if not self.llm_api_key:
            return False
        return True


@dataclass
class LinkedInConfig:
    """LinkedIn credentials configuration."""

    username: str = ""
    password: str = ""

    @property
    def is_logged_in(self) -> bool:
        """Check if credentials are configured."""
        return bool(self.username and self.password)


@dataclass
class SecureConfig:
    """Complete secure configuration."""

    linkedin: LinkedInConfig = field(default_factory=LinkedInConfig)
    ai: AIConfig = field(default_factory=AIConfig)


def _load_env_file() -> None:
    """
    Load environment variables from .env file if it exists.
    This is done automatically by python-dotenv if installed.
    """
    env_path = Path(".env")
    if env_path.exists():
        try:
            from dotenv import load_dotenv

            load_dotenv(env_path)
        except ImportError:
            # Fallback: manually load .env file
            with open(env_path, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ.setdefault(key.strip(), value.strip())


def _get_env_bool(value: str, default: bool = False) -> bool:
    """Convert environment variable to boolean."""
    return value.lower() in ("true", "1", "yes", "on")


def _get_env_value(key: str, default: str = "") -> str:
    """Get environment variable with fallback."""
    return os.environ.get(key, default)


@lru_cache(maxsize=1)
def get_config() -> SecureConfig:
    """
    Get the complete secure configuration.
    Loads values from environment variables.

    Environment Variables:
        LINKEDIN_USERNAME: LinkedIn email
        LINKEDIN_PASSWORD: LinkedIn password
        USE_AI: Enable AI features (true/false)
        AI_PROVIDER: AI provider (openai/deepseek/gemini)
        LLM_API_URL: LLM API endpoint
        LLM_API_KEY: LLM API key
        LLM_MODEL: Model name
        LLM_SPEC: API specification
        STREAM_OUTPUT: Stream AI output (true/false)

    Returns:
        SecureConfig: Complete configuration object
    """
    _load_env_file()

    linkedin_config = LinkedInConfig(
        username=_get_env_value("LINKEDIN_USERNAME", ""),
        password=_get_env_value("LINKEDIN_PASSWORD", ""),
    )

    ai_config = AIConfig(
        use_AI=_get_env_bool(_get_env_value("USE_AI", "False")),
        ai_provider=_get_env_value("AI_PROVIDER", "deepseek"),
        llm_api_url=_get_env_value("LLM_API_URL", "https://api.deepseek.com/v1"),
        llm_api_key=_get_env_value("LLM_API_KEY", ""),
        llm_model=_get_env_value("LLM_MODEL", "deepseek-chat"),
        llm_spec=_get_env_value("LLM_SPEC", "openai"),
        stream_output=_get_env_bool(_get_env_value("STREAM_OUTPUT", "False")),
    )

    return SecureConfig(linkedin=linkedin_config, ai=ai_config)


def get_linkedin_credentials() -> tuple[str, str]:
    """
    Get LinkedIn credentials from secure configuration.

    Returns:
        tuple: (username, password)
    """
    config = get_config()
    return config.linkedin.username, config.linkedin.password


def get_ai_config() -> AIConfig:
    """Get AI configuration from secure configuration."""
    return get_config().ai


def clear_config_cache() -> None:
    """
    Clear the configuration cache.
    Useful for testing or reloading configuration.
    """
    get_config.cache_clear()


# Convenience accessors for backward compatibility
def get_linkedin_username() -> str:
    """Get LinkedIn username."""
    return get_config().linkedin.username


def get_linkedin_password() -> str:
    """Get LinkedIn password."""
    return get_config().linkedin.password


def get_llm_api_key() -> str:
    """Get LLM API key."""
    return get_config().ai.llm_api_key


def use_ai() -> bool:
    """Check if AI is enabled."""
    return get_config().ai.use_AI


def get_ai_provider() -> str:
    """Get AI provider name."""
    return get_config().ai.ai_provider


if __name__ == "__main__":
    # Test configuration loading
    config = get_config()
    print("LinkedIn Configuration:")
    print(f"  Username: {'***' if config.linkedin.username else 'Not set'}")
    print(f"  Password: {'***' if config.linkedin.password else 'Not set'}")
    print("\nAI Configuration:")
    print(f"  Use AI: {config.ai.use_AI}")
    print(f"  Provider: {config.ai.ai_provider}")
    print(f"  API URL: {config.ai.llm_api_url}")
    print(f"  Model: {config.ai.llm_model}")
    print(f"  Configured: {config.ai.is_configured}")
