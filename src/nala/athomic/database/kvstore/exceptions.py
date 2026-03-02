# src/nala/athomic/database/kvstore/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class KVStoreError(AthomicError):
    """Base exception for all errors related to the KV Store."""

    pass


class StoreConnectionError(KVStoreError):
    """Raised when it is not possible to connect to the storage service."""

    pass


class StoreTimeoutError(KVStoreError):
    """Raised when an operation exceeds the expected timeout."""

    pass


class StoreOperationError(KVStoreError):
    """Raised for other operational errors during interaction with the store."""

    pass
