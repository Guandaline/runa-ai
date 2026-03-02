# tests/unit/nala/athomic/database/kvstore/wrappers/test_key_resolving_kv_client.py
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nala.athomic.config.schemas.app_settings import ContextSettings
from nala.athomic.config.schemas.database.kvstore import KeyResolvingWrapperSettings
from nala.athomic.database.kvstore.protocol import KVStoreProtocol
from nala.athomic.database.kvstore.wrappers.key_resolver_kv_client import (
    KeyResolvingKVClient,
)

CONTEXT_VARS_GET_TENANT_PATH = "nala.athomic.context.context_vars.get_tenant_id"
CONTEXT_VARS_GET_USER_PATH = "nala.athomic.context.context_vars.get_user_id"


@pytest.fixture
def mock_client() -> MagicMock:
    client = MagicMock(spec=KVStoreProtocol)
    client.get = AsyncMock()
    client.set = AsyncMock()
    client.delete = AsyncMock()
    client.exists = AsyncMock(return_value=True)
    client.clear = AsyncMock()
    client.is_available = AsyncMock(return_value=True)
    client.service_name = "MockKVStore"
    return client


@pytest.mark.asyncio
@patch(CONTEXT_VARS_GET_USER_PATH, return_value="u1")
@patch(CONTEXT_VARS_GET_TENANT_PATH, return_value="t1")
async def test_key_resolution_for_set_and_get(
    mock_get_tenant_id: MagicMock,
    mock_get_user_id: MagicMock,
    mock_client: MagicMock,
):
    context_settings = ContextSettings(multi_tenancy_enabled=True, use_user_uid=True)
    wrapper_settings = KeyResolvingWrapperSettings(
        namespace="cache", static_prefix="nala"
    )

    wrapper = KeyResolvingKVClient(
        mock_client,
        wrapper_settings=wrapper_settings,
        context_settings=context_settings,
    )

    await wrapper.set("key1", "value", ttl=10)
    await wrapper.get("key1")
    expected_key = "nala:t1:u1:cache:key1"
    mock_client.set.assert_awaited_once_with(expected_key, "value", ttl=10, nx=False)
    mock_client.get.assert_awaited_once_with(expected_key)


@pytest.mark.asyncio
@patch(CONTEXT_VARS_GET_USER_PATH, return_value=None)
@patch(CONTEXT_VARS_GET_TENANT_PATH, return_value="demo")
async def test_delete_and_exists(
    mock_get_tenant_id: MagicMock,
    mock_get_user_id: MagicMock,
    mock_client: MagicMock,
):
    context_settings = ContextSettings(multi_tenancy_enabled=True, use_user_uid=True)
    wrapper_settings = KeyResolvingWrapperSettings(namespace="rl", static_prefix="nala")

    wrapper = KeyResolvingKVClient(
        mock_client,
        wrapper_settings=wrapper_settings,
        context_settings=context_settings,
    )
    await wrapper.delete("x")
    await wrapper.exists("x")
    expected_resolved_key = "nala:demo:rl:x"
    mock_client.delete.assert_awaited_once_with(expected_resolved_key)
    mock_client.exists.assert_awaited_once_with(expected_resolved_key)


@pytest.mark.asyncio
async def test_clear_and_is_available(mock_client):
    wrapper_settings = KeyResolvingWrapperSettings()

    wrapper = KeyResolvingKVClient(mock_client, wrapper_settings=wrapper_settings)

    await wrapper.clear()
    await wrapper.is_available()
    mock_client.clear.assert_awaited_once()
    mock_client.is_available.assert_awaited_once()
