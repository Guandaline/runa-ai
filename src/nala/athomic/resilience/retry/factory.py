# nala/athomic/resilience/retry/factory.py
from typing import Any, Callable, Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.resilience.retry_config import (
    RetryPolicySettings,
    RetrySettings,
)
from nala.athomic.observability.log import get_logger

from .adapter import create_policy_from_settings
from .decorator import retry
from .handler import RetryHandler
from .policy import RetryPolicy

logger = get_logger(__name__)


class RetryFactory:
    """
    Factory class for creating retry policies and decorators for resilient operations.
    """

    def __init__(self, settings: Optional[RetrySettings] = None) -> None:
        self.settings: RetrySettings = settings or get_settings().resilience.retry
        self.logger = logger

    def create_policy(self, name: Optional[str] = None) -> RetryPolicy:
        """
        Creates a RetryPolicy instance based on a named policy from settings.

        In MESH mode, this returns a NoOpRetryPolicy (single attempt).
        """
        if not self.settings:
            raise ValueError("Retry settings are not configured")

        if not name:
            return create_policy_from_settings(self.settings.default_policy)

        if name not in self.settings.policies:
            raise ValueError(f"Retry policy '{name}' not found in settings.")

        policy_settings: RetryPolicySettings
        self.logger.debug(f"Using named retry policy: '{name}'")
        policy_settings = self.settings.policies[name]

        return create_policy_from_settings(policy_settings)

    def create_retry_handler(
        self,
        policy_name: Optional[str] = None,
        operation_name: Optional[str] = None,
        **kwargs: Any,
    ) -> RetryHandler:
        """
        Creates a RetryHandler instance configured with a specific named policy.
        """
        policy = self.create_policy(name=policy_name)

        self.logger.info(f"Creating RetryHandler for operation '{operation_name}'.")
        return RetryHandler(policy=policy, operation_name=operation_name, **kwargs)

    def create_retry_decorator(
        self,
        *,
        policy: Optional[RetryPolicy] = None,
        operation_name: Optional[str] = None,
        logger: Optional[Any] = None,
        tracer: Optional[Any] = None,
        on_retry: Optional[Callable] = None,
        on_fail: Optional[Callable] = None,
        circuit_breaker_hook: Optional[Callable[[BaseException], None]] = None,
        **policy_overrides,
    ):
        """
        Creates the retry decorator.
        """
        used_policy = policy or self.create_policy(**policy_overrides)

        return retry(
            policy=used_policy,
            operation_name=operation_name,
            logger=logger,
            tracer=tracer,
            on_retry=on_retry,
            on_fail=on_fail,
            circuit_breaker_hook=circuit_breaker_hook,
        )
