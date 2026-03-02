from typing import Any, Dict, Optional

from nala.athomic.config.schemas.ai.prompts import PromptSettings
from nala.athomic.observability import get_logger
from nala.athomic.services.base import BaseService

from .io.factory import PromptLoaderFactory
from .io.protocol import PromptLoaderProtocol
from .render.factory import PromptRendererFactory
from .render.protocol import PromptRendererProtocol
from .types import PromptTemplate

logger = get_logger(__name__)


class PromptService(BaseService):
    """
    The main Service for the Prompts module.

    This service acts as the central orchestrator, managing the lifecycle of
    prompts within the application. It decouples the sourcing of templates
    (Loader) from their processing (Renderer).

    Attributes:
        settings (PromptSettings): Module configuration.
        _loader (PromptLoaderProtocol): The configured infrastructure provider for loading templates.
        _renderer (PromptRendererProtocol): The configured engine for text interpolation.
    """

    def __init__(self, settings: PromptSettings):
        """
        Initializes the PromptService.

        Args:
            settings (PromptSettings): The configuration object for the module.
        """
        super().__init__(service_name="prompt_service", enabled=settings.enabled)
        self.settings = settings

        # Initialize components via Factories
        self._loader: PromptLoaderProtocol = PromptLoaderFactory.create(settings)
        self._renderer: PromptRendererProtocol = PromptRendererFactory.create(settings)

        logger.info(
            f"PromptService initialized. Loader: '{settings.backend}', Renderer: '{settings.renderer}'"
        )

    async def _connect(self) -> None:
        """
        Lifecycle method to initialize resources.
        Currently, a no-op as FileSystemLoader and JinjaRenderer are stateless.
        Future loaders (e.g., Redis/Mongo) might need connection logic here.
        """
        # If the loader has a connect method (from BaseServiceProtocol), await it
        if hasattr(self._loader, "connect"):
            await self._loader.connect()  # type: ignore
        await self.set_ready()

    async def _close(self) -> None:
        """Lifecycle method to clean up resources."""
        if hasattr(self._loader, "close"):
            await self._loader.close()  # type: ignore
        logger.info("PromptService shutdown complete.")

    def get_template(self, name: str, version: Optional[str] = None) -> PromptTemplate:
        """
        Retrieves the raw prompt template definition without rendering.

        Args:
            name (str): The unique identifier of the prompt.
            version (Optional[str]): Specific semantic version. Resolves latest if None.

        Returns:
            PromptTemplate: The DTO containing raw text and metadata.
        """
        return self._loader.get(name, version=version)

    def render(
        self, name: str, variables: Dict[str, Any], version: Optional[str] = None
    ) -> str:
        """
        Loads a prompt template and renders it into a final string.

        This is the primary method used by other modules (e.g., AI/LLM services)
        to generate the text payload for model inference.

        Args:
            name (str): The unique identifier of the prompt.
            variables (Dict[str, Any]): The context variables to inject into the template.
            version (Optional[str]): Specific semantic version. Resolves latest if None.

        Returns:
            str: The fully rendered and interpolated string.

        Raises:
            PromptNotFoundError: If the prompt/version does not exist.
            RenderError: If rendering fails (e.g., missing variables).
            TemplateSyntaxError: If the stored template has invalid syntax.
        """
        # 1. Load Data (Infrastructure)
        template = self._loader.get(name, version=version)

        # 2. Process Logic (Renderer)
        return self._renderer.render(template, variables)
