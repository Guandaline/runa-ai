# src/nala/athomic/resilience/locking/exceptions.py


class LockAcquisitionError(Exception):
    """Raised when a distributed lock cannot be acquired within the specified timeout."""

    def __init__(self, key: str, timeout: int):
        self.key = key
        self.timeout = timeout
        super().__init__(f"Could not acquire lock for key '{key}' within {timeout}s.")
