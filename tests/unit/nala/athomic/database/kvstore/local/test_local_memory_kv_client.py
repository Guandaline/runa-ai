import asyncio

import pytest

from nala.athomic.config.schemas.database.kvstore.kvstore_config import KVStoreSettings
from nala.athomic.config.schemas.database.kvstore.providers.local_config import (
    LocalSettings,
)
from nala.athomic.database.kvstore.providers.local.client import LocalKVClient


@pytest.fixture()
def kv() -> LocalKVClient:
    settings = KVStoreSettings(provider=LocalSettings())
    return LocalKVClient(settings=settings)


@pytest.mark.asyncio
async def test_set_and_get_key(kv: LocalKVClient):
    await kv.set("foo", "bar")
    result = await kv.get("foo")
    assert result == "bar"


@pytest.mark.asyncio
async def test_key_expiration(kv: LocalKVClient):
    await kv.set("temp", "123", ttl=1)
    await asyncio.sleep(1.5)
    result = await kv.get("temp")
    assert result is None


@pytest.mark.asyncio
async def test_delete_key(kv: LocalKVClient):
    await kv.set("to-delete", "value")
    await kv.delete("to-delete")
    assert await kv.get("to-delete") is None


@pytest.mark.asyncio
async def test_exists_key(kv: LocalKVClient):
    await kv.set("exists", "yes")
    assert await kv.exists("exists") is True
    await kv.delete("exists")
    assert await kv.exists("exists") is False


@pytest.mark.asyncio
async def test_clear_all_keys(kv: LocalKVClient):
    await kv.set("a", 1)
    await kv.set("b", 2)
    await kv.clear()
    assert await kv.get("a") is None
    assert await kv.get("b") is None


@pytest.mark.asyncio
async def test_is_available(kv: LocalKVClient):
    assert await kv.is_available() is True
