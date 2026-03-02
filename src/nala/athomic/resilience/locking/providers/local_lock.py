# src/nala/athomic/resilience/locking/providers/local_lock.py

import asyncio
import time
from collections import defaultdict
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from nala.athomic.observability.decorators import with_observability
from nala.athomic.observability.log import get_logger
from nala.athomic.observability.metrics import MetricStatus
from nala.athomic.observability.metrics.usage.locking_metrics import (
    locking_attempts_total,
    locking_hold_duration_seconds,
)

from ..protocol import LockingProtocol

logger = get_logger(__name__)


class LocalLockProvider(LockingProtocol):
    """
    An in-memory implementation of the `LockingProtocol`.

    This provider uses standard `asyncio.Lock` objects, making it suitable for
    local development, testing, and single-process applications. It does NOT
    provide distributed locking across multiple instances.
    """

    # Uses a defaultdict to lazily create a new asyncio.Lock for each unique key
    _locks: defaultdict[str, asyncio.Lock] = defaultdict(asyncio.Lock)

    @asynccontextmanager
    @with_observability(
        name="locking.provider.local.acquire", attributes_from_args={"key": "lock.key"}
    )
    async def acquire(self, key: str, timeout: int = 30) -> AsyncGenerator[None, None]:
        """
        Acquires an in-memory asynchronous lock for the given key.

        The operation includes full observability (metrics and tracing).

        Args:
            key (str): The unique resource identifier to be locked.
            timeout (int): The maximum time (in seconds) to wait to acquire the lock.

        Yields:
            None: Execution context for the protected operation.

        Raises:
            TimeoutError: If the lock cannot be acquired within the specified timeout.
        """
        lock = self._locks[key]
        start_time = time.monotonic()
        status = MetricStatus.FAILURE

        try:
            # Wait for the lock acquisition within the specified timeout
            async with asyncio.timeout(timeout):
                await lock.acquire()

            status = MetricStatus.SUCCESS
            logger.debug(f"In-memory lock acquired for key: {key}")
            yield
        except TimeoutError:
            logger.error(f"Timeout acquiring in-memory lock for key '{key}'")
            # Re-raise TimeoutError as expected by the caller (LockingDecorator)
            raise
        finally:
            duration = time.monotonic() - start_time

            # Record the total number of attempts and status
            locking_attempts_total.labels(
                lock_name=key, backend="in_memory", status=status
            ).inc()

            # Record the hold duration only for successfully acquired locks
            if status == MetricStatus.SUCCESS:
                locking_hold_duration_seconds.labels(
                    lock_name=key, backend="in_memory"
                ).observe(duration)

            # Ensure the lock is released, even if the user's protected block raises an exception
            if lock.locked():
                lock.release()
            logger.debug(f"In-memory lock released for key: {key}")
