# tests/unit/nala/athomic/performance/cache/test_cache_result_jitter.py

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.performance.cache.decorators import cache

CACHE_FACTORY_PATH = (
    "nala.athomic.performance.cache.factory.CacheFallbackFactory.create"
)
APPLY_JITTER_PATH = "nala.athomic.performance.cache.handlers.cache_handler.apply_jitter"


@pytest.mark.asyncio
async def test_cache_result_with_jitter_applies_jitter():
    # Arrange
    cache_mock = AsyncMock()
    cache_mock.get.return_value = None
    cache_mock.set.return_value = None

    async def slow_fn(x):
        await asyncio.sleep(0.01)
        return x * 2

    with patch(CACHE_FACTORY_PATH, return_value=cache_mock):
        with patch(APPLY_JITTER_PATH, return_value=42) as jitter_mock:
            # Act
            decorated = cache(ttl=60, use_jitter=True)(slow_fn)
            result = await decorated(5)

            # Assert
            assert result == 10
            jitter_mock.assert_called_once_with(60)
            cache_mock.set.assert_awaited_once()

            args, kwargs = cache_mock.set.await_args
            stored_value_envelope = args[1]
            assert isinstance(stored_value_envelope, dict)
            assert stored_value_envelope["value"] == 10
            assert "expires_at" in stored_value_envelope
            assert kwargs["ttl"] == 42


@pytest.mark.asyncio
async def test_cache_result_without_jitter_uses_exact_ttl():
    # Arrange
    cache_mock = AsyncMock()
    cache_mock.get.return_value = None
    cache_mock.set.return_value = None

    async def compute(x):
        await asyncio.sleep(0.01)
        return x + 1

    with patch(CACHE_FACTORY_PATH, return_value=cache_mock):
        # Act
        decorated = cache(ttl=30, use_jitter=False)(compute)
        result = await decorated(1)

        # Assert
        assert result == 2
        cache_mock.set.assert_awaited_once()
        args, kwargs = cache_mock.set.await_args

        stored_value_envelope = args[1]
        assert stored_value_envelope["value"] == 2
        assert kwargs["ttl"] == 30
