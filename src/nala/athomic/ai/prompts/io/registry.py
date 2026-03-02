from typing import Type

from nala.athomic.base.registry import BaseRegistry

from .loaders.filesystem import FileSystemPromptLoader
from .protocol import PromptLoaderProtocol


class PromptLoaderRegistry(BaseRegistry[Type[PromptLoaderProtocol]]):
    """
    Registry for Prompt Loader implementations.
    """

    def register_defaults(self) -> None:
        """Registers the default system loaders."""
        self.register("filesystem", FileSystemPromptLoader)


# Singleton instance
prompt_loader_registry = PromptLoaderRegistry(protocol=PromptLoaderProtocol)
