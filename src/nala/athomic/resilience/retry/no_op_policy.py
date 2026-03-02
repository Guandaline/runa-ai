from nala.athomic.config.schemas.resilience.retry_config import (
    RetryPolicySettings,
)
from nala.athomic.observability import get_logger

from .adapter import create_policy_from_settings
from .policy import RetryPolicy

logger = get_logger(__name__)


class NoOpRetryPolicy(RetryPolicy):
    """
    A retry policy that performs no retries (single attempt).
    Used in MESH mode to avoid 'retry storms'.
    """

    def __init__(self) -> None:
        # We construct a policy configuration that allows only 1 attempt.
        # This assumes the underlying library (tenacity) interprets stop_after_attempt(1)
        # as "execute once, fail if error".
        settings = RetryPolicySettings(max_attempts=1)
        # We invoke the adapter to get a valid internal policy object
        real_policy = create_policy_from_settings(settings)

        # We copy attributes from the real policy to self to act as a proxy
        # Assuming RetryPolicy is a wrapper or dataclass around tenacity logic
        self.__dict__.update(real_policy.__dict__)

        logger.info("NoOpRetryPolicy initialized")
