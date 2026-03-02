# src/nala/athomic/enums/policies.py
"""Defines standardized enumeration for security and resilience policy names."""

from enum import Enum


class PolicyNames(str, Enum):
    """
    Defines standardized string constants for security and resilience policies.

    Using this enum ensures consistency when referencing authorization policies
    across decorators, registries, and configuration.
    """

    PUBLIC = "public"
    PRIVATE = "private"
    INTERNAL = "internal"
    SHARED_API_KEY = "shared_api_key"  # pragma: allowlist secret
    DB_API_KEY = "db_api_key"  # pragma: allowlist secret
