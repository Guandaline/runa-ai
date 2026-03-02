# src/nala/athomic/ai/tools/registry.py
from typing import Any, Dict, List

from nala.athomic.ai.tools.exceptions import ToolNotFoundError
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.base.instance_registry import BaseInstanceRegistry
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class ToolRegistry(BaseInstanceRegistry[AIToolProtocol]):
    """
    Central repository for registered AI tools.

    Inherits from BaseInstanceRegistry to standardize registration,
    retrieval, and lifecycle management of tool instances.
    """

    def __init__(self) -> None:
        """
        Initialize the registry enforcing the AIToolProtocol.
        """
        super().__init__(protocol=AIToolProtocol)

    def get_definitions(self) -> List[Dict[str, Any]]:
        """
        Returns the list of tool definitions (schemas) formatted for LLM Providers.

        Iterates over all registered tools and extracts their schema metadata
        if they are enabled.

        Returns:
            List[Dict[str, Any]]: A list of tool definitions compatible with
            OpenAI/Vertex tools payload.
        """
        definitions = []
        # self.all() comes from BaseInstanceRegistry
        for tool in self.all().values():
            # BaseService provides is_enabled()
            if tool.is_enabled():
                definitions.append(
                    {
                        "name": tool.name,
                        "description": tool.description,
                        "parameters": tool.schema,
                    }
                )
        return definitions

    def get_tool(self, name: str) -> AIToolProtocol:
        """
        Wrapper around get() to raise a specific ToolNotFoundError
        instead of returning None or raising generic errors.
        """
        try:
            return self.get(name)
        except ValueError:
            raise ToolNotFoundError(f"Tool '{name}' not found in registry.")


# Global singleton instance
tool_registry = ToolRegistry()
