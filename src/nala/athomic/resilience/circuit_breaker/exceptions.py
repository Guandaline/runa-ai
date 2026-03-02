# src/nala/athomic/resilience/circuit_breaker/exceptions.py
"""
Exceptions related to Circuit Breaker, re-exported from the base library.
"""

import aiobreaker

CircuitBreakerError = aiobreaker.CircuitBreakerError

__all__ = ["CircuitBreakerError"]
