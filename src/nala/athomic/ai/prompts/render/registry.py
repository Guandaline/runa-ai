from typing import Type

from nala.athomic.base.registry import BaseRegistry

from .protocol import PromptRendererProtocol
from .providers.jinja_renderer import JinjaPromptRenderer


class PromptRendererRegistry(BaseRegistry[Type[PromptRendererProtocol]]):
    """
    Registry for Prompt Renderer implementations.
    """

    def register_defaults(self) -> None:
        self.register("jinja2", JinjaPromptRenderer)


# Singleton instance
prompt_renderer_registry = PromptRendererRegistry(protocol=PromptRendererProtocol)
