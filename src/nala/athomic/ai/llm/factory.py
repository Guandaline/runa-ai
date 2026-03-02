# src/nala/athomic/ai/llm/factory.py
from nala.athomic.config.schemas.ai.llm.llm_settings import LLMConnectionSettings

from .base import BaseLLM
from .registry import llm_registry


class LLMFactory:
    """
    Factory responsible for creating instances of the configured LLM provider.
    """

    @classmethod
    def create(cls, settings: LLMConnectionSettings) -> BaseLLM:
        """
        Creates and returns an instance of the LLM provider based on the settings.

        Args:
            settings: The specific connection settings containing the backend type
                      and provider-specific configurations.

        Returns:
            An initialized instance adhering to BaseLLM.

        Raises:
            ValueError: If the backend is not specified or not registered.
        """
        backend = settings.backend

        if not backend:
            raise ValueError("LLM backend is not specified in settings.")

        provider_class = llm_registry.get(backend)

        if not provider_class:
            raise ValueError(f"LLM provider '{backend}' is not registered.")

        return provider_class(connection_settings=settings)
