# tests/unit/nala/athomic/ai/agents/persistence/test_unit_kv_provider.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from nala.athomic.ai.agents.persistence.providers.kv import KVCheckpoint
from nala.athomic.database.kvstore.protocol import KVStoreProtocol

pytestmark = pytest.mark.asyncio


@pytest.fixture
def mock_kv_store():
    return MagicMock(spec=KVStoreProtocol)


@pytest.fixture
def kv_checkpoint(mock_kv_store):
    return KVCheckpoint(
        kv_store=mock_kv_store,
        namespace="test_agent",
        ttl_seconds=3600,
    )


async def test_save_flow_success(kv_checkpoint, mock_kv_store):
    """
    Scenario: Saving state should pass the RAW dictionary to KVStore.
    The KVCheckpoint delegates serialization to the infrastructure layer.
    """
    # Arrange
    thread_id = "thread-123"
    state = {"step": 1, "vars": {"a": 1}}
    mock_kv_store.set = AsyncMock()

    # Act
    await kv_checkpoint.save(thread_id, state)

    # Assert
    # 1. Serializer should NOT be called by the provider anymore
    # (implied by not checking it, or explicit assert_not_called if desired)

    # 2. KV Store called with RAW dictionary
    expected_key = "test_agent:thread-123"
    mock_kv_store.set.assert_awaited_once_with(
        key=expected_key,
        value=state,
        ttl=3600,  # Expecting the dict, not bytes
    )


async def test_load_flow_hit(kv_checkpoint, mock_kv_store):
    """
    Scenario: Loading existing state should return the object returned by KVStore.
    """
    # Arrange
    thread_id = "thread-123"
    expected_key = "test_agent:thread-123"
    expected_state = {"mock": "data"}

    # Mock KVStore returning an already deserialized dict (simulating BaseKVStore behavior)
    mock_kv_store.get = AsyncMock(return_value=expected_state)

    # Act
    result = await kv_checkpoint.load(thread_id)

    # Assert
    mock_kv_store.get.assert_awaited_once_with(expected_key)
    assert result == expected_state


async def test_load_flow_miss(kv_checkpoint, mock_kv_store):
    """
    Scenario: Loading non-existent state should return None.
    """
    # Arrange
    mock_kv_store.get = AsyncMock(return_value=None)

    # Act
    result = await kv_checkpoint.load("unknown_thread")

    # Assert
    assert result is None


async def test_delete_flow(kv_checkpoint, mock_kv_store):
    """
    Scenario: Deleting state should remove the key from KVStore.
    """
    # Arrange
    thread_id = "thread-del"
    mock_kv_store.delete = AsyncMock()

    # Act
    await kv_checkpoint.delete(thread_id)

    # Assert
    mock_kv_store.delete.assert_awaited_once_with("test_agent:thread-del")
