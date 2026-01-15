"""
AI Client Module for LinkedIn Auto Job Applier

Unified interface for AI providers (OpenAI, DeepSeek, Gemini).

Usage:
    from src.linkedin_applier.ai.client import AIClient

    client = AIClient(provider="deepseek")
    skills = client.extract_skills(job_description)
    answer = client.answer_question(question, context)
"""

import sys
from pathlib import Path
from typing import Optional, Dict, List, Any, Union
from dataclasses import dataclass
from enum import Enum

# Add project root to path for config imports
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from config import secure_config
from ..utils.logger import log
from ..exceptions import AIConnectionError, AIResponseError


class AIProvider(Enum):
    """Supported AI providers."""

    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    GEMINI = "gemini"


@dataclass
class AIResponse:
    """Response from AI provider."""

    success: bool
    content: Optional[str] = None
    error: Optional[str] = None
    tokens_used: int = 0


class AIClient:
    """
    Unified AI client that supports multiple providers.

    Attributes:
        provider: Current AI provider
        client: Actual provider client
    """

    def __init__(
        self,
        provider: Optional[str] = None,
        api_key: Optional[str] = None,
        model: Optional[str] = None,
    ):
        """
        Initialize the AI client.

        Args:
            provider: AI provider name (openai, deepseek, gemini)
            api_key: API key for the provider
            model: Model name to use
        """
        # Load from config if not provided
        config = secure_config.get_config()

        self.provider = provider or config.ai.ai_provider
        self.api_key = api_key or config.ai.llm_api_key
        self.model = model or config.ai.llm_model
        self.api_url = config.ai.llm_api_url
        self.stream = config.ai.stream_output

        self.client = None
        self._initialize_client()

    def _initialize_client(self) -> None:
        """Initialize the underlying provider client."""
        try:
            if self.provider == "deepseek":
                self._init_deepseek()
            elif self.provider == "openai":
                self._init_openai()
            elif self.provider == "gemini":
                self._init_gemini()
            else:
                log.warning(f"Unknown AI provider: {self.provider}, defaulting to deepseek")
                self._init_deepseek()
        except Exception as e:
            log.warning(f"Failed to initialize AI client: {e}")

    def _init_deepseek(self) -> None:
        """Initialize DeepSeek client."""
        try:
            from modules.ai.deepseekConnections import deepseek_create_client

            self.client = deepseek_create_client()
        except ImportError:
            # Fallback to OpenAI-compatible client
            self._init_openai()

    def _init_openai(self) -> None:
        """Initialize OpenAI client."""
        try:
            from modules.ai.openaiConnections import ai_create_openai_client

            self.client = ai_create_openai_client()
        except Exception as e:
            raise AIConnectionError(f"Failed to initialize OpenAI client: {e}")

    def _init_gemini(self) -> None:
        """Initialize Gemini client."""
        try:
            from modules.ai.geminiConnections import gemini_create_client

            self.client = gemini_create_client()
        except Exception as e:
            raise AIConnectionError(f"Failed to initialize Gemini client: {e}")

    def extract_skills(self, job_description: str) -> Dict[str, Any]:
        """
        Extract skills from job description using AI.

        Args:
            job_description: Text of job description

        Returns:
            Dictionary with skills list
        """
        try:
            if not self.client:
                raise AIConnectionError("AI client not initialized")

            if self.provider == "deepseek":
                from modules.ai.deepseekConnections import deepseek_extract_skills

                result = deepseek_extract_skills(self.client, job_description, stream=self.stream)
            elif self.provider == "openai":
                from modules.ai.openaiConnections import ai_extract_skills

                result = ai_extract_skills(self.client, job_description, stream=self.stream)
            elif self.provider == "gemini":
                from modules.ai.geminiConnections import gemini_extract_skills

                result = gemini_extract_skills(self.client, job_description)
            else:
                raise AIResponseError(f"Unknown provider: {self.provider}")

            if isinstance(result, dict) and "error" in result:
                raise AIResponseError(result["error"])

            return result or {}

        except Exception as e:
            log.error("Failed to extract skills", error=str(e))
            return {"error": str(e)}

    def answer_question(
        self,
        question: str,
        options: Optional[List[str]] = None,
        question_type: str = "text",
        job_description: Optional[str] = None,
        about_company: Optional[str] = None,
        user_info: Optional[str] = None,
    ) -> str:
        """
        Generate answer for a question using AI.

        Args:
            question: Question text
            options: Available options for select/radio
            question_type: Type of question
            job_description: Job description for context
            about_company: Company info for context
            user_info: User info for context

        Returns:
            Generated answer
        """
        try:
            if not self.client:
                raise AIConnectionError("AI client not initialized")

            if self.provider == "deepseek":
                from modules.ai.deepseekConnections import deepseek_answer_question

                result = deepseek_answer_question(
                    self.client,
                    question,
                    options,
                    question_type,
                    job_description,
                    about_company,
                    user_info,
                    stream=self.stream,
                )
            elif self.provider == "openai":
                from modules.ai.openaiConnections import ai_answer_question

                result = ai_answer_question(
                    self.client,
                    question,
                    options,
                    question_type,
                    job_description,
                    about_company,
                    user_info,
                    stream=self.stream,
                )
            elif self.provider == "gemini":
                from modules.ai.geminiConnections import gemini_answer_question

                result = gemini_answer_question(
                    self.client,
                    question,
                    options,
                    question_type,
                    job_description,
                    about_company,
                    user_info,
                )
            else:
                raise AIResponseError(f"Unknown provider: {self.provider}")

            if isinstance(result, dict) and "error" in result:
                raise AIResponseError(result["error"])

            return str(result) if result else ""

        except Exception as e:
            log.error("Failed to answer question", error=str(e))
            raise AIResponseError(f"Failed to generate answer: {e}")

    def close(self) -> None:
        """Close the AI client and cleanup."""
        try:
            if self.provider in ["openai", "deepseek"]:
                # OpenAI-compatible clients don't need explicit close
                pass
            elif self.provider == "gemini":
                # Gemini doesn't have a close method
                pass
        except Exception as e:
            log.warning(f"Error closing AI client: {e}")

    def is_available(self) -> bool:
        """Check if AI client is available."""
        return self.client is not None


def create_ai_client(provider: Optional[str] = None) -> AIClient:
    """
    Factory function to create an AI client.

    Args:
        provider: AI provider name

    Returns:
        Configured AIClient instance
    """
    return AIClient(provider=provider)


if __name__ == "__main__":
    print("AIClient module created successfully")
    print("\\nFeatures:")
    print("  - extract_skills(job_description)")
    print("  - answer_question(question, options, ...)")
    print("  - close()")
    print("  - is_available()")
    print("  - create_ai_client(provider)")
