# src/nala/athomic/ai/tools/function_tool.py
import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, Optional

from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.ai.tools.exceptions import InvalidToolArgumentsError
from nala.athomic.ai.tools.schema import SchemaGenerator


class FunctionTool(BaseTool):
    """
    A concrete Tool implementation that wraps a Python function.
    Handles runtime validation and type coercion using Pydantic.
    """

    def __init__(
        self,
        func: Callable[..., Any],
        name: Optional[str] = None,
        description: Optional[str] = None,
    ):
        tool_name = name or func.__name__
        tool_description = description or (func.__doc__ or "").strip()

        super().__init__(name=tool_name, description=tool_description)

        self._func = func
        # Create the Pydantic model for runtime validation
        self._args_model = SchemaGenerator.create_arguments_model(func)
        # Generate the JSON schema for the LLM
        self._schema = SchemaGenerator.generate(func)
        self._is_coroutine = inspect.iscoroutinefunction(func)

    @property
    def schema(self) -> Dict[str, Any]:
        return self._schema

    async def _execute_tool(self, **kwargs: Any) -> Any:
        """
        Executes the wrapped function.

        1. Validates and converts arguments using the Pydantic model.
        2. Calls the function (sync or async).
        """
        try:
            # Pydantic magic: converts strings to Enums, casts types, checks required fields
            validated_args = self._args_model(**kwargs)
        except Exception as e:
            raise InvalidToolArgumentsError(
                f"Arguments validation failed for tool '{self.name}': {e}"
            ) from e

        # Extract native Python objects (Enums, ints, etc.) from the model
        function_kwargs = validated_args.model_dump()

        if self._is_coroutine:
            return await self._func(**function_kwargs)
        else:
            loop = asyncio.get_running_loop()
            return await loop.run_in_executor(
                None, functools.partial(self._func, **function_kwargs)
            )
