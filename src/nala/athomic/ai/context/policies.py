from abc import ABC, abstractmethod
from datetime import datetime
from typing import Dict

from nala.athomic.context import context_vars
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class TokenLimitPolicy(ABC):
    """
    Abstract contract for strategies that adjust token limits dynamically.
    Follows the Strategy Pattern.
    """

    @abstractmethod
    def apply(self, current_limit: int, model_name: str) -> int:
        """
        Applies a limit adjustment based on the policy logic.

        Args:
            current_limit: The limit resolved so far.
            model_name: The name of the model being used.

        Returns:
            int: The adjusted (potentially lower) token limit.
        """
        pass


class TierBasedLimitPolicy(TokenLimitPolicy):
    """
    Adjusts limits based on the tenant/user tier found in the execution context.
    Configuration is passed via init, ensuring reusability.
    """

    def __init__(self, tier_limits: Dict[str, int], default_tier: str = "default"):
        """
        Args:
            tier_limits: Map of 'tier_name' -> 'max_tokens'.
                         e.g., {'free': 4096, 'pro': 128000}
        """
        self.tier_limits = {k.lower(): v for k, v in tier_limits.items()}
        self.default_tier = default_tier

    def apply(self, current_limit: int, model_name: str) -> int:
        # Resolve tier from context (Standard Nala Context Pattern)
        # Assuming 'role' or a dedicated 'tier' context var is used.
        user_tier = context_vars.get_role() or self.default_tier

        tier_cap = self.tier_limits.get(user_tier.lower())

        if tier_cap is None:
            # If tier not found, do not enforce this policy
            return current_limit

        # Apply the tightest constraint
        effective_limit = min(current_limit, tier_cap)

        if effective_limit < current_limit:
            logger.debug(
                f"[Policy] Tier '{user_tier}' capped limit: {current_limit} -> {effective_limit}"
            )

        return effective_limit


class PeakHourPolicy(TokenLimitPolicy):
    """
    Reduces limits during specific hours to manage infrastructure load.
    """

    def __init__(self, start_hour: int, end_hour: int, reduction_factor: float = 0.5):
        self.start_hour = start_hour
        self.end_hour = end_hour
        self.reduction_factor = reduction_factor

    def apply(self, current_limit: int, model_name: str) -> int:
        now_hour = datetime.now().hour

        if self.start_hour <= now_hour < self.end_hour:
            throttled = int(current_limit * self.reduction_factor)
            logger.info(
                f"[Policy] Peak Hour ({self.start_hour}-{self.end_hour}h) active. "
                f"Throttling: {current_limit} -> {throttled}"
            )
            return throttled

        return current_limit
