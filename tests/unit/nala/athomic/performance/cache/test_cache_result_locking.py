# tests/unit/nala/athomic/performance/cache/test_cache_result_locking.py

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.performance.cache.decorators import cache
from nala.athomic.resilience.locking.protocol import LockingProtocol

CACHE_FACTORY_PATH = (
    "nala.athomic.performance.cache.factory.CacheFallbackFactory.create"
)
LOCKING_FACTORY_PATH = "nala.athomic.resilience.locking.factory.LockingFactory.create"


@pytest.mark.asyncio
async def test_cache_result_with_lock_prevents_thundering_herd():
    """
    Tests that when a cache item is missed, only the first of multiple concurrent
    callers executes the function, while others wait and use the cached result.
    """
    call_count = 0
    store = {}

    async def expensive_func(x):
        nonlocal call_count
        # Simulate a slow I/O-bound operation
        await asyncio.sleep(0.02)
        call_count += 1
        return x * 10

    # Mock the cache provider to use our in-memory 'store'
    mock_cache = AsyncMock()

    async def fake_get(key):
        await asyncio.sleep(0.01)
        return store.get(key)

    async def fake_set(key, value, ttl):
        store[key] = value
        await asyncio.sleep(0.01)

    mock_cache.get.side_effect = fake_get
    mock_cache.set.side_effect = fake_set

    shared_lock = asyncio.Lock()
    mock_lock_provider = AsyncMock(spec=LockingProtocol)
    mock_lock_provider.acquire.return_value = shared_lock

    with (
        patch(CACHE_FACTORY_PATH, return_value=mock_cache),
        patch(
            LOCKING_FACTORY_PATH, return_value=mock_lock_provider
        ) as mock_create_lock,
    ):
        decorated = cache(ttl=30, use_lock=True)(expensive_func)

        # Act: Run two calls to the same function concurrently
        results = await asyncio.gather(decorated(1), decorated(1))

        # Assert
        assert results == [
            10,
            10,
        ], "Both calls should return the correct computed value."
        assert mock_create_lock.call_count >= 1
        mock_lock_provider.acquire.assert_called()

        assert call_count == 1
