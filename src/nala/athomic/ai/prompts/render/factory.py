from nala.athomic.config.schemas.ai.prompts import PromptSettings
from nala.athomic.observability import get_logger

from .protocol import PromptRendererProtocol
from .registry import prompt_renderer_registry

logger = get_logger(__name__)


class PromptRendererFactory:
    """
    Factory responsible for creating the configured Prompt Renderer instance.
    """

    @classmethod
    def create(cls, settings: PromptSettings) -> PromptRendererProtocol:
        """
        Instantiates the specific renderer based on settings.renderer.
        """
        renderer_name = settings.renderer.lower()

        logger.debug(f"Initializing Prompt Renderer: '{renderer_name}'")

        renderer_cls = prompt_renderer_registry.get(renderer_name)

        if not renderer_cls:
            raise ValueError(f"Prompt Renderer '{renderer_name}' is not registered.")

        # Jinja renderer doesn't strictly need settings currently, but
        # following the pattern, we instantiate it.
        return renderer_cls()
