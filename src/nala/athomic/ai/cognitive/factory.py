# src/nala/athomic/ai/cognitive/factory.py
from typing import Optional

from nala.athomic.ai.cognitive.base import CognitiveBaseService
from nala.athomic.ai.cognitive.registry import cognitive_registry
from nala.athomic.ai.llm.manager import llm_manager
from nala.athomic.ai.prompts.factory import PromptServiceFactory
from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class CognitiveFactory:
    """
    Factory for creating the appropriate Cognitive Service implementation.
    """

    @classmethod
    def create(
        cls, settings: Optional[CognitiveSettings] = None
    ) -> CognitiveBaseService:
        """
        Instantiates the Cognitive Service based on the configured strategy.
        """
        settings = settings or get_settings().ai.cognitive

        try:
            # 1. Resolve Common Dependencies
            llm = llm_manager.get_client()
            prompt_service = PromptServiceFactory.create()

            # 2. Resolve Service Class from Registry
            # The registry maps 'llm' -> LLMCognitiveService class
            service_cls = cognitive_registry.get(settings.strategy)

            # 3. Instantiate the Service
            service = service_cls(
                llm=llm,
                prompt_service=prompt_service,
                settings=settings,
            )

            logger.success(
                f"CognitiveService initialized (Strategy: {settings.strategy})"
            )
            return service

        except Exception as e:
            logger.critical(f"Failed to create CognitiveService: {e}")
            raise RuntimeError("CognitiveService creation failed") from e
