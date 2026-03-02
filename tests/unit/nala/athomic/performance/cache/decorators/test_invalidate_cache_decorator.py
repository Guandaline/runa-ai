# tests/unit/nala/athomic/performance/cache/decorators/test_invalidate_cache_decorator.py

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.performance.cache.cache_key_resolver import CacheKeyGenerator
from nala.athomic.performance.cache.decorators import invalidate_cache
from nala.athomic.performance.cache.protocol import CacheProtocol

CACHE_FACTORY_PATH = (
    "nala.athomic.performance.cache.factory.CacheFallbackFactory.create"
)


@pytest.mark.asyncio
async def test_invalidate_cache_with_decorator_prefix():
    """
    Checks if @invalidate_cache uses the key_prefix provided in the decorator
    to build the key to be invalidated.
    """
    # Arrange
    decorator_prefix = "items:v2"
    deleted_keys = []

    async def fake_delete(key):
        deleted_keys.append(key)
        await asyncio.sleep(0.01)  # Simulates network latency

    async def update_item(item_id: int):
        await asyncio.sleep(0.01)  # Simulates a slow operation
        return f"updated item {item_id}"

    # 1. Mock the cache provider
    mock_cache_provider_instance = AsyncMock(spec=CacheProtocol)
    mock_cache_provider_instance.delete.side_effect = fake_delete

    # 2. Mock CacheFallbackFactory to return our mocked provider
    with patch(CACHE_FACTORY_PATH, return_value=mock_cache_provider_instance):
        # 3. Apply the decorator with the specific key_prefix
        decorated_func = invalidate_cache(key_prefix=decorator_prefix)(update_item)

        # 4. Execute the decorated function
        await decorated_func(456)

        # Assert
        assert (
            len(deleted_keys) == 1
        ), "mock_cache_provider_instance.delete was not called"

        captured_key = deleted_keys[0]

        # Dynamically generate the expected key to ensure consistency
        expected_base_key = CacheKeyGenerator.for_function(update_item, (456,), {})
        expected_key = f"{decorator_prefix}:{expected_base_key}"

        assert captured_key == expected_key


@pytest.mark.asyncio
async def test_invalidate_cache_without_any_prefix():
    """
    Checks if @invalidate_cache generates a key without prefix when none is provided.
    """
    # Arrange
    deleted_keys = []

    async def fake_delete(key):
        await asyncio.sleep(0.01)
        deleted_keys.append(key)

    async def delete_user_data(user_id: str):
        await asyncio.sleep(0.01)
        return "deleted"

    mock_cache_provider_instance = AsyncMock(spec=CacheProtocol)
    mock_cache_provider_instance.delete.side_effect = fake_delete

    with patch(CACHE_FACTORY_PATH, return_value=mock_cache_provider_instance):
        # Apply the decorator WITHOUT key_prefix
        decorated_func = invalidate_cache()(delete_user_data)

        # Act
        await decorated_func("user-abc")

        # Assert
        assert len(deleted_keys) == 1
        captured_key = deleted_keys[0]

        # Dynamically generate the expected key
        expected_key = CacheKeyGenerator.for_function(
            delete_user_data, ("user-abc",), {}
        )

        assert captured_key == expected_key
