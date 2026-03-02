# src/nala/athomic/ai/llm/registry.py
from typing import Type

from nala.athomic.ai.llm.protocol import LLMProviderProtocol
from nala.athomic.base.registry import BaseRegistry
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class LLMProviderRegistry(BaseRegistry[Type[LLMProviderProtocol]]):
    """
    Registry for LLM (Large Language Model) provider implementations.
    Maps backend strings (e.g., 'vertex', 'openai') to their respective provider classes.
    """

    def register_defaults(self) -> None:
        """
        Registers the default supported providers.
        Imports are done locally to avoid circular dependencies during initialization.
        """
        from .providers.google_genai_provider import GoogleGenAIProvider
        from .providers.openai_provider import OpenAIProvider

        self.register("google_genai", GoogleGenAIProvider)
        self.register("openai", OpenAIProvider)
        self.register("ollama", OpenAIProvider)
        self.register("azure", OpenAIProvider)

        logger.debug("Default LLM providers registered: 'vertex', 'openai'.")


llm_registry = LLMProviderRegistry(protocol=LLMProviderProtocol)
