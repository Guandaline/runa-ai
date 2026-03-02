# src/nala/athomic/ai/llm/factory_manager.py
from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai import AISettings
from nala.athomic.observability import get_logger

from .manager import LLMManager

logger = get_logger(__name__)


class LLMManagerFactory:
    """
    Factory responsible for creating and managing the singleton instance
    of the LLMManager.

    It acts as the composition root for the LLM core service.
    """

    _instance: Optional[LLMManager] = None

    @classmethod
    def create(cls, settings: Optional[AISettings] = None) -> LLMManager:
        """
        Creates or returns the existing singleton instance of LLMManager.

        Args:
            settings: Optional configuration overrides. If None, loads from global settings.

        Returns:
            The initialized singleton instance of LLMManager.

        Raises:
            RuntimeError: If the AI section is disabled in settings.
        """
        if cls._instance is not None:
            return cls._instance

        logger.debug("Creating LLMManager singleton...")

        effective_settings = settings or get_settings().ai

        if not effective_settings.enabled:
            raise RuntimeError("AI module is disabled in application settings.")

        try:
            instance = LLMManager(settings=effective_settings)
            cls._instance = instance
            logger.success("LLMManager singleton created and configured successfully.")
            return cls._instance

        except Exception as e:
            logger.exception("Failed to initialize LLMManager.")
            raise RuntimeError(f"Could not create LLMManager: {e}") from e

    @classmethod
    async def clear(cls) -> None:
        """
        Resets the singleton instance and stops the underlying manager if active.
        """
        if cls._instance:
            logger.debug("Stopping and clearing LLMManager singleton.")
            await cls._instance.stop()
            cls._instance = None
