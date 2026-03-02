import asyncio
import json
from typing import Any, Callable, List

from pydantic import BaseModel

from nala.athomic.ai.agents.executors.base import BaseToolExecutor
from nala.athomic.ai.schemas import ToolCall, ToolOutput
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class SyncToolExecutor(BaseToolExecutor):
    """
    Executes tools synchronously or concurrently within the asyncio event loop.

    Enhanced to robustly serialize complex return types (Pydantic models, Dicts)
    into valid JSON strings for optimal LLM consumption.
    """

    async def execute_batch(self, tool_calls: List[ToolCall]) -> List[ToolOutput]:
        """
        Executes a batch of tool calls concurrently.

        Args:
            tool_calls: A list of ToolCall objects requesting execution.

        Returns:
            A list of ToolOutput objects containing results or errors.
        """
        logger.info("Executing batch of {} tool calls.", len(tool_calls))
        # Use asyncio.gather to run independent tools in parallel
        tasks = [self._execute_single_safe(tc) for tc in tool_calls]
        return await asyncio.gather(*tasks)

    async def _execute_single_safe(self, tool_call: ToolCall) -> ToolOutput:
        """
        Executes a single tool with exception safety and smart serialization.

        Args:
            tool_call: The tool invocation request.

        Returns:
            The execution result or error formatted as ToolOutput.
        """
        tool_name = tool_call.name
        arguments = tool_call.arguments
        tool = self._get_tool(tool_name)

        if not tool:
            return self._create_error_output(
                tool_call, f"Tool '{tool_name}' is not registered or available."
            )

        try:
            logger.debug("Invoking tool '{}' with provided arguments.", tool_name)

            executable_func = self._resolve_executable(tool)

            # Execute the tool (handling both sync and async definitions)
            if asyncio.iscoroutinefunction(executable_func):
                result = await executable_func(**arguments)
            else:
                # Offload synchronous work to a thread to avoid blocking the loop
                result = await asyncio.to_thread(executable_func, **arguments)

            # Serialize result to a format the LLM can understand (JSON preferred)
            content = self._serialize_result(result)

            return ToolOutput(
                tool_call_id=tool_call.id,
                name=tool_name,
                content=content,
                # Optionally store the raw result if needed for internal logic (non-LLM)
                result_metadata={"raw_type": type(result).__name__},
            )

        except Exception as e:
            logger.error(
                "Exception during execution of tool '{}': {}",
                tool_name,
                e,
                exc_info=True,
            )
            return self._create_error_output(tool_call, str(e))

    def _serialize_result(self, result: Any) -> str:
        """
        Converts execution results into a string representation optimized for LLMs.

        Prioritizes JSON serialization for structured data.
        """
        if result is None:
            return "Success (No output)"

        if isinstance(result, str):
            return result

        # Handle Pydantic Models directly
        if isinstance(result, BaseModel):
            return result.model_dump_json()

        # Handle Dicts/Lists via JSON dumping
        if isinstance(result, (dict, list, tuple)):
            try:
                return json.dumps(result, default=str, ensure_ascii=False)
            except (TypeError, ValueError):
                logger.warning(
                    "JSON serialization failed for tool result. Falling back to str()."
                )

        # Fallback to string representation
        return str(result)

    def _resolve_executable(self, tool: Any) -> Callable[..., Any]:
        """
        Resolves the callable method from a tool instance.

        Raises:
            AttributeError: If the tool has no executable method.
        """
        if hasattr(tool, "execute"):
            return tool.execute
        if hasattr(tool, "run"):
            return tool.run
        if callable(tool):
            return tool

        raise AttributeError(f"Tool '{type(tool).__name__}' has no executable method.")
