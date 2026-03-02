# tests/unit/nala/athomic/database/kvstore/providers/local/test_local_kv_client.py
import pytest

from nala.athomic.config.schemas.database.kvstore import KVStoreSettings, LocalSettings
from nala.athomic.database.kvstore.providers.local.client import LocalKVClient


@pytest.fixture
def local_client():
    settings = KVStoreSettings(provider=LocalSettings(backend="local"))
    return LocalKVClient(settings=settings)


@pytest.mark.asyncio
class TestLocalKVClientHashes:
    async def test_hset_and_hgetall(self, local_client):
        # Arrange
        key = "my_hash"
        field1 = "field1"
        value1 = "value1"
        field2 = "field2"
        value2 = "value2"

        # Act - Set fields
        # hset returns 1 if new field, 0 if updated
        res1 = await local_client.hset(key, field1, value1)
        res2 = await local_client.hset(key, field2, value2)

        # Act - Update existing field
        res3 = await local_client.hset(key, field1, "new_value1")

        # Assert returns
        assert res1 == 1
        assert res2 == 1
        assert res3 == 0

        # Act - Retrieve all
        result = await local_client.hgetall(key)

        # Assert data
        # Note: BaseKVStore serializer handles serialization, but LocalKVClient stores bytes internally if passed directly to _hset.
        # However, public .hset() calls serializer.
        # Since we are testing the public API, values returned by .hgetall() are deserialized.
        # Let's assume checking the final deserialized values.
        assert result == {"field1": "new_value1", "field2": "value2"}

    async def test_hgetall_empty(self, local_client):
        result = await local_client.hgetall("non_existent_hash")
        assert result == {}

    async def test_hdel(self, local_client):
        # Arrange
        key = "hash_to_delete"
        await local_client.hset(key, "f1", "v1")
        await local_client.hset(key, "f2", "v2")
        await local_client.hset(key, "f3", "v3")

        # Act - Delete mixed existing and non-existing fields
        # Should return number of fields actually removed
        deleted_count = await local_client.hdel(key, ["f1", "f3", "non_existent"])

        # Assert
        assert deleted_count == 2

        # Verify remaining
        remaining = await local_client.hgetall(key)
        assert remaining == {"f2": "v2"}

    async def test_hdel_removes_key_if_empty(self, local_client):
        # Arrange
        key = "cleanup_hash"
        await local_client.hset(key, "f1", "v1")

        # Act
        await local_client.hdel(key, ["f1"])

        # Assert - Key should be gone from internal storage logic (though public API doesn't expose key existence check for hashes directly besides exists())
        exists = await local_client.exists(key)
        assert exists is False
