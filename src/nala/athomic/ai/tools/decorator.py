# src/nala/athomic/ai/tools/decorator.py
from typing import Any, Callable, Optional, Union

from nala.athomic.ai.tools.function_tool import FunctionTool
from nala.athomic.ai.tools.registry import tool_registry


def ai_tool(
    func: Optional[Callable[..., Any]] = None,
    *,
    name: Optional[str] = None,
    description: Optional[str] = None,
    auto_register: bool = True,
) -> Union[Callable[..., Any], FunctionTool]:
    """
    Decorator to convert a Python function into an AITool service.

    The decorated function is wrapped in a `FunctionTool` instance (which is a BaseService)
    and registered in the global `tool_registry`.

    Usage:
        @ai_tool
        def my_tool(arg: int): ...

    Args:
        func: The function being decorated.
        name: Optional custom name for the tool.
        description: Optional custom description.
        auto_register: If True (default), registers the tool to the global registry.

    Returns:
        The `FunctionTool` instance wrapping the original function.
    """

    def decorator(f: Callable[..., Any]) -> FunctionTool:
        tool_instance = FunctionTool(f, name=name, description=description)

        if auto_register:
            # BaseInstanceRegistry.register(name, item_instance)
            tool_registry.register(name=tool_instance.name, item_instance=tool_instance)

        return tool_instance

    if func is None:
        return decorator

    return decorator(func)
