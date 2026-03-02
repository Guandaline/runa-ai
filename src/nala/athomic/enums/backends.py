# src/nala/athomic/enums/backends.py
"""Defines standardized enumeration for backend provider names."""

from enum import Enum


class Backends(str, Enum):
    """
    Defines standardized string constants for backend provider names.

    Using this enum ensures type safety and prevents errors from typos when
    referencing backend implementations in configuration and code.
    """

    # Messaging Backends
    KAFKA = "kafka"
    LOCAL_MESSAGING = "local"

    # Storage Backends
    LOCAL_STORAGE = "local"
    GCS = "gcs"

    # Secrets Backends
    VAULT = "vault"
    ENV = "env"
    FILE = "file"
    ENV_ENCRYPTED = "env_encrypted"

    # Database Backends
    MONGO = "mongo"
    REDIS = "redis"

    # HTTP Client Backends
    HTTPX = "httpx"

    # Compression Backends
    GZIP = "gzip"
    BROTLI = "brotli"

    # Task/Scheduler Backends
    TASKIQ = "taskiq"
    RQ = "rq"
    DRAMATIQ = "dramatiq"
    CUSTOM_KV = "custom_kv"

    # Resilience/Control Backends
    IN_MEMORY = "in_memory"
    LIMITS = "limits"
    CONSUL = "consul"

    # Generic/Strategy Names
    STANDARD = "standard"
    MESSAGING = "messaging"
    NOOP = "noop"
    JWT = "jwt"
    API_KEY_SHARED = "api_key_shared"  # pragma: allowlist secret
    API_KEY_DB = "api_key_db"  # pragma: allowlist secret
