# nala/athomic/context/propagation.py

from contextlib import contextmanager
from typing import Any, Dict, Generator, Optional

from nala.athomic.observability import get_logger

# Import the singleton manager, which is the source of truth for context variables
from .manager import context_var_manager

logger = get_logger(__name__)


def capture_context() -> Dict[str, Any]:
    """
    Captures the current values of all context variables marked for propagation.

    This function iterates through the centrally registered context variables
    in the `context_var_manager`, collects the values of those flagged with
    `propagate=True`, and returns them as a dictionary. This dictionary is
    suitable for serialization and passing to background tasks or events.

    Returns:
        A dictionary containing the current context values to be propagated.
    """
    propagated_context = {}
    # Get all variables that should be propagated from the central manager
    for name, info in context_var_manager.get_propagated_vars().items():
        value = info.var.get()
        # Only include non-None values in the captured context to keep the payload clean
        if value is not None:
            propagated_context[name] = value

    logger.trace(f"Context captured for propagation: {propagated_context}")
    return propagated_context


@contextmanager
def restore_context(
    context_dict: Optional[Dict[str, Any]],
) -> Generator[None, None, None]:
    """
    A context manager to temporarily set context variables from a dictionary.

    This is used on the worker side (e.g., in a background task or event handler)
    to re-establish the context that existed when the job was enqueued.
    It safely resets all variables to their previous state upon exiting the `with` block.

    Args:
        context_dict: The dictionary of context values captured before the
                      task was enqueued.
    """
    if not context_dict:
        yield
        return

    tokens: Dict[str, Any] = {}
    logger.trace(f"Attempting to restore context from: {context_dict}")

    for key, value in context_dict.items():
        # The manager handles setting the value on the correct ContextVar
        token = context_var_manager.set(key, value)
        if token:
            tokens[key] = token

    try:
        yield
    finally:
        logger.trace("Resetting context variables after execution.")
        # Reset variables in reverse order of setting to maintain stack-like behavior
        for key, token in reversed(tokens.items()):
            context_var_manager.reset(key, token)
