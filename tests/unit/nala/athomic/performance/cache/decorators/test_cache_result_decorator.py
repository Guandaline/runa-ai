# tests/unit/nala/athomic/performance/cache/decorators/test_cache_result_decorator.py

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.performance.cache.cache_key_resolver import CacheKeyGenerator
from nala.athomic.performance.cache.decorators import cache
from nala.athomic.performance.cache.protocol import CacheProtocol

CACHE_FACTORY_PATH = (
    "nala.athomic.performance.cache.factory.CacheFallbackFactory.create"
)


@pytest.mark.asyncio
async def test_cache_result_with_decorator_prefix():
    """
    Checks if @cache uses the key_prefix provided in the decorator
    to build the final logical key.
    """
    # Arrange
    decorator_prefix = "users:v1"
    captured_set_keys = []

    async def fake_get(key):
        await asyncio.sleep(0.01)
        return None

    async def fake_set(key, value, ttl=None):
        await asyncio.sleep(0.01)
        captured_set_keys.append(key)

    async def get_user_by_id(user_id: int):
        await asyncio.sleep(0.01)
        return {"id": user_id, "name": "Test User"}

    mock_cache_provider_instance = AsyncMock(spec=CacheProtocol)
    mock_cache_provider_instance.get.side_effect = fake_get
    mock_cache_provider_instance.set.side_effect = fake_set
    mock_cache_provider_instance.service_name = "mock_cache_provider"

    with patch(CACHE_FACTORY_PATH, return_value=mock_cache_provider_instance):
        decorated_func = cache(
            ttl=30,
            key_prefix=decorator_prefix,
        )(get_user_by_id)

        # Act
        await decorated_func(123)

        # Assert
        assert (
            len(captured_set_keys) == 1
        ), "The mock_cache_provider_instance.set was not called"

        captured_key = captured_set_keys[0]

        expected_base_key = CacheKeyGenerator.for_function(get_user_by_id, (123,), {})
        expected_key = f"{decorator_prefix}:{expected_base_key}"

        assert captured_key == expected_key


@pytest.mark.asyncio
async def test_cache_result_without_any_prefix():
    """
    Check if @cache generates a key without a prefix when none is provided.
    """
    # Arrange
    captured_set_keys = []

    async def fake_get(key):
        await asyncio.sleep(0.01)
        return None

    async def fake_set(key, value, ttl=None):
        await asyncio.sleep(0.01)
        captured_set_keys.append(key)

    async def get_some_data():
        await asyncio.sleep(0.01)
        return "data"

    mock_cache_provider_instance = AsyncMock(spec=CacheProtocol)
    mock_cache_provider_instance.get.side_effect = fake_get
    mock_cache_provider_instance.set.side_effect = fake_set
    mock_cache_provider_instance.service_name = "mock_cache_provider"

    with patch(CACHE_FACTORY_PATH, return_value=mock_cache_provider_instance):
        decorated_func = cache(ttl=30)(get_some_data)

        # Act
        await decorated_func()

        # Assert
        assert len(captured_set_keys) == 1
        captured_key = captured_set_keys[0]

        expected_key = CacheKeyGenerator.for_function(get_some_data, (), {})

        assert captured_key == expected_key
