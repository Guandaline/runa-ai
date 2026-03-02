# src/nala/athomic/ai/tools/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class ToolError(AthomicError):
    """Base exception for all tool-related errors."""

    pass


class ToolExecutionError(ToolError):
    """
    Raised when the tool's internal logic fails during execution.
    Captures the original exception for debugging context.
    """

    def __init__(self, tool_name: str, original_error: Exception):
        self.tool_name = tool_name
        self.original_error = original_error
        super().__init__(f"Error executing tool '{tool_name}': {original_error}")


class InvalidToolArgumentsError(ToolError):
    """
    Raised when the arguments provided to the tool do not match
    its expected schema (validation failure).
    """

    pass


class ToolNotFoundError(ToolError):
    """Raised when requesting a tool that is not registered."""

    pass
