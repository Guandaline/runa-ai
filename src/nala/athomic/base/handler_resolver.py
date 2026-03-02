import importlib
from typing import Callable

from .exceptions import AthomicError


class HandlerResolutionError(AthomicError):
    """
    Raised when a handler path cannot be resolved to a valid callable.
    """

    pass


class HandlerResolver:
    """
    Resolves a fully qualified string path into a callable handler.

    This resolver is intentionally strict: only callable objects are accepted.
    Any resolution error is raised eagerly to fail fast during bootstrap
    instead of at execution time.
    """

    def resolve(self, path: str) -> Callable:
        """
        Resolves and validates a handler from its fully qualified path.

        Args:
            path (str): Fully qualified import path
                        (e.g. "my_module.submodule.my_handler").

        Returns:
            Callable: A callable handler object.

        Raises:
            HandlerResolutionError: If the path is invalid, cannot be imported,
            or does not resolve to a callable.
        """
        try:
            module_path, attribute_name = path.rsplit(".", 1)
        except ValueError as exc:
            raise HandlerResolutionError(
                f"Invalid handler path '{path}'. Expected format: <module>.<attribute>."
            ) from exc

        try:
            module = importlib.import_module(module_path)
        except ImportError as exc:
            raise HandlerResolutionError(
                f"Failed to import module '{module_path}' while resolving handler '{path}'."
            ) from exc

        try:
            handler = getattr(module, attribute_name)
        except AttributeError as exc:
            raise HandlerResolutionError(
                f"Handler attribute '{attribute_name}' not found in module '{module_path}'."
            ) from exc

        if not callable(handler):
            raise HandlerResolutionError(
                f"Resolved object '{path}' is not callable (type: {type(handler).__name__})."
            )

        return handler


default_handler_resolver = HandlerResolver()
