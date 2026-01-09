"""
Common utilities for AI services.

This module provides shared components used across AI service modules:
- MissingAPIKeyError: Exception for missing API key configuration
- get_genai_client: Factory function for Google GenAI client initialization
- Common constants and defaults
"""

from google import genai

from app.core.config import settings

# Configuration defaults (centralized from settings)
DEFAULT_MODEL_NAME = settings.GEMINI_GRAPH_MODEL
DEFAULT_MODEL_TEMPERATURE = settings.GEMINI_GRAPH_TEMPERATURE
DEFAULT_MAX_RETRY_ATTEMPTS = settings.GEMINI_GRAPH_MAX_RETRY_ATTEMPTS


class MissingAPIKeyError(Exception):
    """Raised when the Google API key is not configured."""

    pass


def get_genai_client(api_key: str | None = None) -> genai.Client:
    """Initialize and return a Google GenAI Client.

    Args:
        api_key: Optional API key override. If not provided,
                 uses settings.GOOGLE_API_KEY.

    Returns:
        Configured genai.Client instance.

    Raises:
        MissingAPIKeyError: If no API key is available.
    """
    api_key = api_key or settings.GOOGLE_API_KEY
    if not api_key:
        raise MissingAPIKeyError(
            "GOOGLE_API_KEY is not set in settings. "
            "Please configure it before running the pipeline."
        )
    return genai.Client(api_key=api_key)
