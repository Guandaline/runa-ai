# File: src/nala/athomic/config/schemas/models.py
"""Defines common Pydantic models and type aliases used across configuration schemas.

This module provides standardized data structures for handling complex
configuration patterns, particularly for secret management.
"""

from typing import Awaitable, Callable, Union

from pydantic import BaseModel, SecretStr


class SecretValue(BaseModel):
    """Represents a structured reference to a secret in an external provider.

    Instead of hardcoding secrets in configuration, this model is used to point
    to a secret's location (e.g., in HashiCorp Vault). The `SecretsManager`
    resolves these references at runtime to fetch the actual secret value.

    Attributes:
        path (str): The path or mount point in the secrets backend where the
            group of secrets is stored (e.g., 'database/production').
        key (str): The specific key within the given path that holds the
            secret value (e.g., 'password').
    """

    path: str
    key: str


# A type alias representing the various forms a secret can take within the configuration.
# - SecretStr: For a raw secret value that Pydantic protects from being exposed in logs.
# - SecretValue: For a structured reference to an external secret.
# - Callable[[], Awaitable[SecretStr]]: For a lazy-loading proxy or async getter
#   that resolves the secret at runtime.
secrets_types = Union[SecretStr, SecretValue, Callable[[], Awaitable[SecretStr]]]
