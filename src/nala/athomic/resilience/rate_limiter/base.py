# Em: src/nala/athomic/resilience/rate_limiter/providers/base.py

from abc import abstractmethod
from typing import Optional

from nala.athomic.config.schemas.resilience.rate_limiter.rate_limiter_config import (
    RateLimiterSettings,
)
from nala.athomic.observability.decorators import with_observability
from nala.athomic.resilience.rate_limiter.protocol import RateLimiterProtocol
from nala.athomic.services import BaseService


class RateLimiterBase(BaseService, RateLimiterProtocol):
    """
    Abstract base class for Rate Limiter Providers.

    This class implements the `ConnectionServiceProtocol` via `BaseService`
    for manageable lifecycle and adds an observability layer
    around the methods of `RateLimiterProtocol`.

    Subclasses must implement the abstract methods with an underscore
    (e.g., `_allow`), which contain the backend-specific logic.
    """

    def __init__(self, settings: RateLimiterSettings, service_name: str):
        """
        Initializes the base provider.

        Args:
            settings: The rate limiter settings.
            service_name: The service name for logging and metrics.
        """
        super().__init__(service_name=service_name, enabled=settings.enabled)
        self.settings = settings

    @with_observability(
        name="rate_limiter.provider.allow",
        attributes_from_args={"key": "ratelimit.key", "rate": "ratelimit.rate"},
    )
    async def allow(self, key: str, rate: str, policy: Optional[str] = None) -> bool:
        """
        Checks if the key is allowed, wrapping the backend logic
        with observability.
        """
        if not self.is_ready():
            self.logger.warning(
                f"Service '{self.service_name}' is not ready. Denying request for key '{key}'."
            )
            return False
        return await self._allow(key, rate)

    @with_observability(
        name="rate_limiter.provider.clear",
        attributes_from_args={"key": "ratelimit.key"},
    )
    async def clear(self, key: str, rate: str) -> None:
        """
        Clears the counter for a key, wrapping the backend logic
        with observability.
        """
        if not self.is_ready():
            self.logger.warning(
                f"Service '{self.service_name}' is not ready. Ignoring clear for key '{key}'."
            )
            return
        await self._clear(key, rate)

    @with_observability(name="rate_limiter.provider.reset")
    async def reset(self) -> None:
        """
        Resets all counters, wrapping the backend logic with observability.
        """
        if not self.is_ready():
            self.logger.warning(
                f"Service '{self.service_name}' is not ready. Ignoring reset."
            )
            return
        await self._reset()

    @with_observability(
        name="rate_limiter.provider.get_current_usage",
        attributes_from_args={"key": "ratelimit.key"},
    )
    async def get_current_usage(self, key: str, rate: str) -> Optional[int]:
        """
        Gets the current usage for a key, wrapping the backend logic
        with observability.
        """
        if not self.is_ready():
            self.logger.warning(
                f"Service '{self.service_name}' is not ready. Returning None for usage of key '{key}'."
            )
            return None
        return await self._get_current_usage(key, rate)

    # --- Abstract Methods for Implementation by Subclasses ---

    @abstractmethod
    async def _allow(self, key: str, rate: str) -> bool:
        """
        Provider-specific implementation logic to check permission.
        """
        raise NotImplementedError

    @abstractmethod
    async def _clear(self, key: str, rate: str) -> None:
        """
        Provider-specific implementation logic to clear a key.
        """
        raise NotImplementedError

    @abstractmethod
    async def _reset(self) -> None:
        """
        Provider-specific implementation logic to reset all counters.
        """
        raise NotImplementedError

    @abstractmethod
    async def _get_current_usage(self, key: str, rate: str) -> Optional[int]:
        """
        Provider-specific implementation logic to get current usage.
        """
        raise NotImplementedError

    # --- BaseService Lifecycle Methods (Optional) ---

    async def _connect(self) -> None:
        """
        Subclasses may implement this function if they need to establish
        a network connection (e.g., with Redis).
        """
        ...

    async def _close(self) -> None:
        """
        Subclasses may implement this function if they need to close
        resources or connections.
        """
        ...
