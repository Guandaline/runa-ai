from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.prompts import PromptSettings
from nala.athomic.observability import get_logger

from .service import PromptService

logger = get_logger(__name__)


class PromptServiceFactory:
    """
    Factory responsible for creating and managing the singleton instance
    of the PromptService.
    """

    _instance: Optional[PromptService] = None

    @classmethod
    def create(cls, settings: Optional[PromptSettings] = None) -> PromptService:
        """
        Creates or returns the existing singleton instance of PromptService.
        """
        if cls._instance is not None:
            if settings:
                logger.warning(
                    "PromptService is already initialized. "
                    "The provided 'settings' argument will be ignored."
                )
            return cls._instance

        logger.debug("Creating PromptService singleton...")

        if settings is None:
            try:
                app_settings = get_settings()
                settings = app_settings.ai.prompts
            except AttributeError:
                logger.critical(
                    "Global AppSettings does not have 'ai.prompts' configured."
                )
                raise RuntimeError(
                    "Configuration error: 'ai.prompts' section missing in AppSettings."
                )

        try:
            if not hasattr(settings, "backend"):
                raise RuntimeError(
                    f"Invalid settings type: {type(settings)}. Expected PromptSettings with a 'backend' field. "
                    "Check if AppSettings is incorrectly using ConnectionGroupSettings."
                )

            instance = PromptService(settings=settings)

            cls._instance = instance

            logger.success(
                f"PromptService initialized successfully (Backend: {settings.backend})"
            )
            return cls._instance

        except Exception as e:
            logger.exception("Failed to initialize PromptService.")
            raise RuntimeError(f"Could not create PromptService: {e}") from e

    @classmethod
    def clear(cls) -> None:
        """
        Clears the singleton instance.
        """
        if cls._instance:
            logger.debug("Clearing PromptService singleton.")
            cls._instance = None
