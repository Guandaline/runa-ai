import time
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.performance.cache.handlers import CacheHandler
from nala.athomic.performance.cache.protocol import CacheProtocol


@pytest.mark.asyncio
@patch("nala.athomic.performance.cache.handlers.cache_handler.asyncio.create_task")
async def test_refresh_ahead_triggers_background_update(mock_create_task: AsyncMock):
    original_function_mock = AsyncMock(return_value="new_value_1")
    mock_cache_provider = AsyncMock(spec=CacheProtocol)

    TTL = 10
    REFRESH_THRESHOLD = 0.8

    stale_expires_at = time.time() + (TTL * (1 - REFRESH_THRESHOLD)) / 2
    initial_cached_value = {
        "value": "stale_value_1",
        "expires_at": stale_expires_at,
    }

    mock_cache_provider.get.return_value = initial_cached_value
    mock_cache_provider.set = AsyncMock()
    mock_cache_provider.service_name = "mock_cache_provider"

    handler = CacheHandler(
        func=original_function_mock,
        args=(1,),
        kwargs={},
        ttl=TTL,
        refresh_ahead=True,
        refresh_threshold=REFRESH_THRESHOLD,
        provider=mock_cache_provider,
        use_jitter=False,
        use_lock=False,
        lock_timeout=5,
    )
    result = await handler.execute()

    assert result == "stale_value_1"
    original_function_mock.assert_not_called()
    mock_create_task.assert_called_once()
    mock_cache_provider.set.assert_not_called()
