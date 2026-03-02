# src/nala/athomic/observability/readiness.py

from typing import Any, Awaitable, Callable, Dict

# Global registry to store check functions, mapped by name
_check_registry: Dict[str, Callable[[], Awaitable[bool]]] = {}


def register_check(name: str) -> Callable[..., Any]:
    """
    Decorator factory to register an asynchronous function as a readiness check.

    The decorated function must be an async function that accepts no arguments
    and should return a boolean (True for 'ok', False for 'fail').

    Args:
        name: The unique, descriptive name for the readiness check (e.g., 'database_connection').

    Returns:
        Callable: The inner decorator function.
    """

    def decorator(func: Callable[[], Awaitable[bool]]) -> Callable[[], Awaitable[bool]]:
        """
        Inner decorator that adds the function to the global registry.
        """
        _check_registry[name] = func
        return func

    return decorator


async def run_readiness_checks() -> Dict[str, str]:
    """
    Executes all registered readiness check functions asynchronously.

    The execution result is mapped to a standardized status string:
    - True: 'ok'
    - False or Exception: 'fail'
    - Any other return value (including None): 'skipped'

    Returns:
        Dict[str, str]: A dictionary of check names mapped to their status
                        ('ok', 'fail', 'skipped').
    """
    results = {}
    for name, check_func in _check_registry.items():
        try:
            result = await check_func()
            if result is True:
                results[name] = "ok"
            elif result is False:
                results[name] = "fail"
            else:
                # Catches None or non-boolean return types, marking them as skipped
                results[name] = "skipped"
        except Exception:
            # Any unhandled exception during the check means the resource is unavailable
            results[name] = "fail"
    return results
