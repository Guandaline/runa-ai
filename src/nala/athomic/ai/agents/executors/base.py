import json
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from nala.athomic.ai.agents.executors.protocol import ToolExecutorProtocol
from nala.athomic.ai.schemas import ToolCall, ToolOutput
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.ai.tools.registry import ToolRegistry
from nala.athomic.observability import get_logger
from nala.athomic.services import BaseService

logger = get_logger(__name__)


class BaseToolExecutor(BaseService, ToolExecutorProtocol, ABC):
    """
    Abstract base class for tool execution strategies.

    Manages the lifecycle of tools and standardizes execution error handling.
    Acts as a Service itself, ensuring all dependent tools are ready when connected.
    """

    def __init__(self, tool_registry: Optional[ToolRegistry] = None):
        """
        Initializes the executor as a service.

        Args:
            tool_registry: Registry containing available tools. If None,
                           a default registry instance is created.
        """
        super().__init__(service_name=f"tool_executor_{self.__class__.__name__}")
        self.tool_registry = tool_registry or ToolRegistry()
        self._active_tools: List[AIToolProtocol] = []

    async def _connect(self) -> None:
        """
        Lifecycle hook: Prepares the executor and initializes all registered tools.

        Iterates through the registry, identifies tools that require lifecycle management
        (instances of BaseService), and connects them. Failures in individual tools
        are logged but do not prevent the executor from starting.
        """
        # Iterate over all registered tools to ensure they are initialized
        # Accessing the internal registry dictionary if available, or list_tools method
        if hasattr(self.tool_registry, "_registry"):
            tools_map = self.tool_registry._registry
        elif hasattr(self.tool_registry, "list_tools"):
            tools_map = self.tool_registry.list_tools()
        else:
            logger.warning(
                "ToolRegistry does not expose tools listing. Skipping tool initialization."
            )
            tools_map = {}

        for tool_name, tool_instance in tools_map.items():
            if isinstance(tool_instance, BaseService):
                try:
                    # Only connect if not already running to avoid state errors
                    if not tool_instance.is_ready() and not tool_instance.is_running():
                        logger.debug("Initializing tool dependency: '{}'", tool_name)
                        await tool_instance.connect()
                        await tool_instance.wait_ready()

                    self._active_tools.append(tool_instance)

                except Exception as e:
                    # Robustness: A single tool failure should not crash the entire Agent/Executor
                    # We log the error and skip this tool. If the Agent tries to use it, it will fail then.
                    logger.error(
                        "Failed to initialize tool '{}': {}. Tool will be unavailable.",
                        tool_name,
                        e,
                    )
            else:
                # Non-service tools are just added to active list (assumed ready)
                self._active_tools.append(tool_instance)

        logger.info(
            "Tool Executor ready with {} active tools.", len(self._active_tools)
        )
        await self.set_ready()

    async def _close(self) -> None:
        """
        Lifecycle hook: Shuts down all active tools managed by this executor.
        """
        for tool in self._active_tools:
            if isinstance(tool, BaseService) and tool.is_ready():
                try:
                    await tool.stop()
                except Exception as e:
                    logger.warning(
                        "Error stopping tool '{}': {}",
                        getattr(tool, "name", "unknown"),
                        e,
                    )

        self._active_tools.clear()
        logger.info("Tool Executor stopped.")

    @abstractmethod
    async def execute_batch(self, tool_calls: List[ToolCall]) -> List[ToolOutput]:
        """
        Executes a batch of tool calls.

        Must be implemented by concrete strategies (e.g., Sync, Async, Parallel).
        """
        pass

    def get_tools_for_agent(self, tool_names: List[str]) -> List[AIToolProtocol]:
        """
        Retrieves and validates a list of tools required by an Agent.

        Args:
            tool_names: List of tool identifiers requested by the agent profile.

        Returns:
            List of ready-to-use tool instances.
        """
        valid_tools = []
        for name in tool_names:
            tool = self.tool_registry.get_tool(name)
            if tool:
                valid_tools.append(tool)
            else:
                logger.warning("Tool '{}' not found in registry.", name)
        return valid_tools

    def _get_tool(self, name: str) -> Any:
        """Retrieves a tool implementation from the registry."""
        return self.tool_registry.get_tool(name)

    def _create_error_output(self, tool_call: ToolCall, error_msg: str) -> ToolOutput:
        """
        Creates a standardized ToolOutput representing an execution failure.

        Args:
            tool_call: The original tool call request.
            error_msg: Description of the error.

        Returns:
            A ToolOutput object with the error details.
        """
        logger.error(
            "Tool execution failed for '{}': {}",
            tool_call.name,
            error_msg,
        )

        return ToolOutput(
            tool_call_id=tool_call.id,
            name=tool_call.name,
            content=json.dumps(
                {
                    "error": "ToolExecutionError",
                    "message": error_msg,
                    "status": "failed",
                }
            ),
        )
