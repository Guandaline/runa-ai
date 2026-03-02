# src/nala/athomic/ai/cognitive/registry.py
from typing import Type

from nala.athomic.base.registry import BaseRegistry
from nala.athomic.observability import get_logger

from .base import CognitiveBaseService

logger = get_logger(__name__)


class CognitiveRegistry(BaseRegistry[Type[CognitiveBaseService]]):
    """
    Registry for Cognitive Service implementations.
    """

    def register_defaults(self) -> None:
        """Registers default service implementations."""
        from .providers.llm import LLMCognitiveService

        self.register("llm", LLMCognitiveService)
        logger.debug("Registered default cognitive service: 'llm'.")


# Domain Singleton
cognitive_registry = CognitiveRegistry(protocol=CognitiveBaseService)
