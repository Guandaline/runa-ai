# src/nala/athomic/resilience/locking/decorator.py

import asyncio
import functools
import inspect
from typing import Any, Callable

from nala.athomic.observability import get_logger

from .exceptions import LockAcquisitionError
from .factory import LockingFactory

logger = get_logger(__name__)


def _resolve_key(key_template: str, func: Callable, args: tuple, kwargs: dict) -> str:
    """
    Resolves the final lock key by formatting the string template with the
    arguments passed to the decorated function.

    Args:
        key_template (str): The f-string template defining the lock key structure.
        func (Callable): The decorated function.
        args (tuple): Positional arguments for the function.
        kwargs (dict): Keyword arguments for the function.

    Returns:
        str: The fully resolved, unique lock key.

    Raises:
        ValueError: If a required argument for the key template is missing.
    """
    try:
        # Get the function signature to map positional arguments to names
        bound_args = inspect.signature(func).bind(*args, **kwargs)
        bound_args.apply_defaults()

        # Create a dictionary with all arguments available for formatting
        all_args = bound_args.arguments

        return key_template.format(**all_args)
    except (KeyError, IndexError) as e:
        logger.error(
            f"Failed to resolve lock key '{key_template}' for function '{func.__name__}'. "
            f"Argument '{e}' not found."
        )
        raise ValueError(f"Missing argument '{e}' to format lock key.") from e


def distributed_lock(key: str, timeout: int = 30) -> Callable:
    """
    Decorator that enforces mutual exclusion for an asynchronous function using a
    distributed lock.

    The decorator ensures that only one call runs at a time for a given unique key,
    preventing race conditions in a distributed environment.

    Args:
        key (str): A template for the lock key. Can use arguments from the
                   decorated function (e.g., "payment:{payment_id}").
        timeout (int): Time (in seconds) to wait to acquire the lock before failing.
                       Defaults to 30 seconds.

    Returns:
        Callable: The decorator function.

    Raises:
        TypeError: If the decorated function is not asynchronous.
    """

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        if not inspect.iscoroutinefunction(func):
            raise TypeError(
                "The @distributed_lock decorator only supports async functions."
            )

        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any) -> Any:
            # 1. Resolve the dynamic key based on function arguments
            resolved_key = _resolve_key(key, func, args, kwargs)

            # 2. Get the configured locking provider instance
            provider = LockingFactory.create()

            logger.debug(f"Attempting to acquire lock for key: '{resolved_key}'")
            try:
                # 3. Use the asynchronous context manager to acquire and release the lock
                async with provider.acquire(resolved_key, timeout=timeout):
                    logger.info(f"Lock acquired for key: '{resolved_key}'")
                    # 4. Execute the protected function logic
                    return await func(*args, **kwargs)

            except asyncio.TimeoutError as e:
                # 5. Catch generic timeout and raise the specific LockAcquisitionError
                logger.warning(f"Timeout acquiring lock for key '{resolved_key}'")
                raise LockAcquisitionError(key=resolved_key, timeout=timeout) from e

        return wrapper

    return decorator
