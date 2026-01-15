"""
Secure Configuration Module for LinkedIn Auto Job Applier

This module handles secure loading of credentials and configuration from environment variables.
"""

import os
from typing import Optional
from dataclasses import dataclass

# Load environment variables from .env file if it exists
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # python-dotenv not installed, continue with system environment variables
    pass


@dataclass
class AIConfig:
    """Configuration for AI services."""
    llm_api_url: str
    llm_model: str
    llm_spec: str
    stream_output: bool


def get_linkedin_username() -> str:
    """Get LinkedIn username from environment variable or fallback."""
    return os.getenv('LINKEDIN_USERNAME', 'your_email@example.com')


def get_linkedin_password() -> str:
    """Get LinkedIn password from environment variable or fallback."""
    return os.getenv('LINKEDIN_PASSWORD', 'your_password')


def use_ai() -> bool:
    """Check if AI should be used."""
    return os.getenv('USE_AI', 'false').lower() in ('true', '1', 'yes')


def get_ai_provider() -> str:
    """Get AI provider from environment variable."""
    return os.getenv('AI_PROVIDER', 'openai')


def get_llm_api_key() -> str:
    """Get LLM API key from environment variable (supports multiple providers)."""
    ai_provider = get_ai_provider().lower()

    # Check provider-specific API keys first
    if ai_provider == 'openai':
        return os.getenv('OPENAI_API_KEY', os.getenv('LLM_API_KEY', ''))
    elif ai_provider == 'deepseek':
        return os.getenv('DEEPSEEK_API_KEY', os.getenv('LLM_API_KEY', ''))
    elif ai_provider == 'gemini':
        return os.getenv('GEMINI_API_KEY', os.getenv('LLM_API_KEY', ''))

    # Fallback to generic LLM_API_KEY
    return os.getenv('LLM_API_KEY', '')


def get_ai_config() -> AIConfig:
    """Get AI configuration."""
    return AIConfig(
        llm_api_url=os.getenv('LLM_API_URL', 'https://api.openai.com/v1'),
        llm_model=os.getenv('LLM_MODEL', 'gpt-3.5-turbo'),
        llm_spec=os.getenv('LLM_SPEC', 'openai'),
        stream_output=os.getenv('STREAM_OUTPUT', 'false').lower() in ('true', '1', 'yes')
    )