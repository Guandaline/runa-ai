# src/nala/athomic/resilience/__init__.py
"""
Nala Athomic Resilience Package

Provides decorators and utilities for building resilient applications,
including Retry, Fallback, Circuit Breaker, and Rate Limiting patterns.
"""

from .circuit_breaker import CircuitBreakerError, circuit_breaker
from .locking import (
    LockAcquisitionError,
    LockingFactory,
    LockingProtocol,
    distributed_lock,
)
from .retry import (
    RetryError,
    RetryFactory,
    RetryHandler,
    RetryPolicy,
    retry,
)

__all__ = [
    # Retry
    "RetryFactory",
    "RetryHandler",
    "RetryPolicy",
    "retry",
    "RetryError",
    # Circuit Breaker
    "circuit_breaker",
    "CircuitBreakerError",
    # Locking
    "distributed_lock",
    "LockAcquisitionError",
    "LockingFactory",
    "LockingProtocol",
]
