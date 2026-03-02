# tests/unit/nala/athomic/database/kvstore/wrappers/test_default_ttl_kv_client.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from nala.athomic.config.schemas.database.kvstore.kvstore_config import (
    KVStoreSettings,
)
from nala.athomic.config.schemas.database.kvstore.wrapper_config import (
    DefaultTTLWrapperSettings,
)
from nala.athomic.database.kvstore.wrappers.default_ttl_kv_client import (
    DefaultTTLKvClient,
)


@pytest.fixture
def mock_base_client() -> AsyncMock:
    """
    Provides a mock for the client that will be wrapped by the wrapper.
    Instead of a strict 'spec', we manually configure the expected attributes
    to reflect both KVStoreProtocol and BaseServiceProtocol.
    """

    client = AsyncMock()
    client.service_name = "MockBaseKVStore"

    client.set = AsyncMock()
    client.get = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock()
    client.clear = AsyncMock()
    client.close = AsyncMock()

    client.is_ready = MagicMock(return_value=True)

    return client


@pytest.fixture
def kvstore_settings() -> KVStoreSettings:
    """Provides a default instance of KVStoreSettings for the tests."""
    return KVStoreSettings(enabled=True)


# ===== Initialization Tests =====


def test_init_with_positive_default_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if a positive default TTL is stored correctly."""
    default_ttl = 3600
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=default_ttl),
    )
    assert wrapper.client is mock_base_client
    assert wrapper.default_ttl == default_ttl


def test_init_with_zero_default_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if a zero default TTL results in None."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=0),
    )
    assert wrapper.default_ttl is None


def test_init_with_negative_default_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if a negative default TTL results in None."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=-60),
    )
    assert wrapper.default_ttl is None


def test_init_with_none_default_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if a None default TTL results in None."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=None),
    )
    assert wrapper.default_ttl is None


# ===== Set Method Tests =====


@pytest.mark.asyncio
async def test_set_with_explicit_positive_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if an explicit positive TTL is passed to the base client."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=3600),
    )
    await wrapper.set("mykey", "myvalue", ttl=60)
    mock_base_client.set.assert_awaited_once_with("mykey", "myvalue", ttl=60, nx=False)


@pytest.mark.asyncio
async def test_set_with_explicit_zero_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if an explicit zero TTL results in ttl=None in the base client."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=3600),
    )
    await wrapper.set("mykey", "myvalue", ttl=0)
    mock_base_client.set.assert_awaited_once_with(
        "mykey", "myvalue", ttl=None, nx=False
    )


@pytest.mark.asyncio
async def test_set_with_explicit_negative_ttl(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if an explicit negative TTL results in ttl=None in the base client."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=3600),
    )
    await wrapper.set("mykey", "myvalue", ttl=-10)
    mock_base_client.set.assert_awaited_once_with(
        "mykey", "myvalue", ttl=None, nx=False
    )


@pytest.mark.asyncio
async def test_set_with_ttl_none_uses_default(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if ttl=None uses the wrapper's default_ttl."""
    default_ttl = 3600
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=default_ttl),
    )
    await wrapper.set("mykey", "myvalue", ttl=None)
    mock_base_client.set.assert_awaited_once_with(
        "mykey", "myvalue", ttl=default_ttl, nx=False
    )


@pytest.mark.asyncio
async def test_set_with_ttl_none_and_no_default(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if ttl=None with no default_ttl results in ttl=None."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(default_ttl_seconds=None),
    )
    await wrapper.set("mykey", "myvalue", ttl=None)
    mock_base_client.set.assert_awaited_once_with(
        "mykey", "myvalue", ttl=None, nx=False
    )


# ===== Other Delegation Method Tests =====


@pytest.mark.asyncio
async def test_get_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if get() delegates to client.get() correctly."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    key = "getkey"
    expected_value = "ret_value"
    mock_base_client.get.return_value = expected_value
    result = await wrapper.get(key)
    assert result == expected_value
    mock_base_client.get.assert_awaited_once_with(key)


@pytest.mark.asyncio
async def test_delete_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if delete() delegates to client.delete() correctly."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    await wrapper.delete("delkey")
    mock_base_client.delete.assert_awaited_once_with("delkey")


@pytest.mark.asyncio
async def test_exists_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if exists() delegates to client.exists() correctly."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    mock_base_client.exists.return_value = True
    result = await wrapper.exists("existskey")
    assert result is True
    mock_base_client.exists.assert_awaited_once_with("existskey")


@pytest.mark.asyncio
async def test_clear_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if clear() delegates to client.clear() correctly."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    await wrapper.clear()
    mock_base_client.clear.assert_awaited_once()


@pytest.mark.asyncio
async def test_is_ready_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if is_ready() delegates correctly."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    # Test for False to ensure the value is being passed
    mock_base_client.is_ready.return_value = False
    result = wrapper.is_ready()
    assert result is False
    # Since the mock was reconfigured, is_ready is now a mock
    mock_base_client.is_ready.assert_called_once()


@pytest.mark.asyncio
async def test_close_delegates(
    mock_base_client: AsyncMock, kvstore_settings: KVStoreSettings
):
    """Checks if close() delegates to the client's close() method."""
    wrapper = DefaultTTLKvClient(
        client=mock_base_client,
        settings=kvstore_settings,
        wrapper_settings=DefaultTTLWrapperSettings(),
    )
    await wrapper.close()
    mock_base_client.close.assert_awaited_once()
