from typing import Optional, Protocol, runtime_checkable


@runtime_checkable
class RateLimiterProtocol(Protocol):
    """
    Defines the interface for a context-aware rate limiter.
    All implementations must respect the allow/clear/reset contract.
    """

    async def allow(self, key: str, rate: str, policy: Optional[str] = None) -> bool:
        """
        Checks if the given key is allowed under the specified rate limit and
        consumes a token if allowed.

        Args:
            key (str): The identifier for the entity being rate limited (e.g., user ID, IP).
            rate (str): The rate limit string (e.g., "5/second", "100/minute").
            policy (Optional[str]): An optional policy identifier to apply specific rate limits.

        Returns:
            bool: True if the request is allowed, False if the rate limit has been exceeded.
        """
        ...

    async def clear(self, key: str, rate: str) -> None:
        """
        Resets the rate limit counters specifically for the given key and rate limit rule.

        Args:
            key (str): The identifier whose rate limit counters to reset.
            rate (str): The rate limit string rule associated with the key to clear
                        (needed to identify the correct counter(s)).
        """
        ...

    async def reset(self) -> None:
        """
        Resets **all** rate limit counters managed by this storage instance.
        WARNING: Use with extreme caution, especially with shared storage like Redis,
                 as this will affect all keys managed by this limiter instance.
        """
        ...

    async def get_current_usage(self, key: str, rate: str) -> Optional[int]:
        """
        Optional: Returns the current usage count for the given key under a specific rate.
        May not be supported by all implementations or strategies.

        Args:
            key (str): The identifier to query.
            rate (str): The rate limit string rule to check usage against.

        Returns:
            Optional[int]: Number of requests used in the window, if supported.
        """
        ...
