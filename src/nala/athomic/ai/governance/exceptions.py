# src/nala/athomic/ai/governance/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class GovernanceError(AthomicError):
    """Base exception for policy violations."""

    pass


class QuotaExceededError(GovernanceError):
    """Raised when a rate limit or budget is exceeded."""

    pass


class SecurityPolicyViolationError(GovernanceError):
    """Raised when content violates security rules (e.g. PII detected)."""

    pass
