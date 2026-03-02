# adapters/retry_policy_adapter.py

from nala.athomic.config.schemas.resilience.retry_config import (
    RetryPolicySettings,
)

from .policy import RetryPolicy


def resolve_exceptions(exception_names):
    """
    Resolves a list or tuple of exception names (as strings) or exception types into a tuple of exception types.

    Args:
        exception_names (list or tuple): A list or tuple containing exception types or their names as strings.

    Returns:
        tuple: A tuple of resolved exception types.

    Raises:
        ValueError: If a string does not correspond to a known built-in exception name.
        TypeError: If an element is neither a string nor an exception type.

    Examples:
        >>> resolve_exceptions(['ValueError', KeyError])
        (<class 'ValueError'>, <class 'KeyError'>)
    """

    import builtins

    resolved = []
    for exc in exception_names:
        if isinstance(exc, type) and issubclass(exc, BaseException):
            resolved.append(exc)
        elif isinstance(exc, str):
            if hasattr(builtins, exc):
                resolved.append(getattr(builtins, exc))
            else:
                raise ValueError(f"Unknown exception name: {exc}")
        else:
            raise TypeError(f"Invalid exception: {exc}")
    return tuple(resolved)


def create_policy_from_settings(settings: RetryPolicySettings) -> RetryPolicy:
    """
    Creates a RetryPolicy instance based on the provided RetryPolicySettings.
    Args:
        settings (RetryPolicySettings): The configuration settings for the retry policy.
    Returns:
        RetryPolicy: The created RetryPolicy instance.
    """
    return RetryPolicy(
        attempts=settings.attempts,
        exceptions=resolve_exceptions(settings.exceptions),
        wait_min_seconds=settings.wait_min_seconds,
        wait_max_seconds=settings.wait_max_seconds,
        backoff=settings.backoff,
        jitter=settings.jitter,
        timeout=settings.timeout,
    )
