# src/nala/athomic/ai/tools/protocol.py
from typing import Any, Dict, Protocol, runtime_checkable

from nala.athomic.services.protocol import BaseServiceProtocol


@runtime_checkable
class AIToolProtocol(BaseServiceProtocol, Protocol):
    """
    Defines the contract for an AI-executable tool.

    Inherits from BaseServiceProtocol to ensure all tools support standard
    lifecycle management (connect/close) and health checks.
    """

    @property
    def name(self) -> str:
        """The unique identifier of the tool (e.g., 'get_weather')."""
        ...

    @property
    def description(self) -> str:
        """Natural language description for the LLM."""
        ...

    @property
    def schema(self) -> Dict[str, Any]:
        """
        The JSON Schema (OpenAPI compatible) defining the arguments.
        Used by the LLM Provider to formulate the tool definition.
        """
        ...

    async def execute(self, **kwargs: Any) -> Any:
        """
        Executes the tool logic asynchronously.

        Args:
            **kwargs: The arguments parsed from the LLM's response.

        Returns:
            The result of the tool execution.
        """
        ...
