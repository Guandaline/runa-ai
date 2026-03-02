from nala.athomic.config.schemas.ai.prompts import PromptSettings
from nala.athomic.observability import get_logger

from .protocol import PromptLoaderProtocol
from .registry import prompt_loader_registry

logger = get_logger(__name__)


class PromptLoaderFactory:
    """
    Factory responsible for creating the configured Prompt Loader instance.
    """

    @classmethod
    def create(cls, settings: PromptSettings) -> PromptLoaderProtocol:
        """
        Instantiates the specific loader based on settings.backend.
        """
        backend = settings.backend.lower()
        logger.debug(f"Initializing Prompt Loader backend: '{backend}'")

        logger.debug(f"\n\n\nPrompt Loader Settings: {settings}\n\n\n")

        # 1. Resolve Class from Registry
        loader_cls = prompt_loader_registry.get(backend)
        if not loader_cls:
            raise ValueError(f"Prompt Loader backend '{backend}' is not registered.")

        # 2. Instantiate with Provider Settings
        # Using the polymorphic 'provider' field from PromptSettings
        return loader_cls(settings=settings.provider)
