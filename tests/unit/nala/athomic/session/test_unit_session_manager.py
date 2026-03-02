import pytest

from nala.athomic.session.manager import SessionManager
from tests.helpers import async_factory, async_on_close


@pytest.mark.asyncio
async def test_manager_creates_session_once():
    manager = SessionManager()
    calls = []

    lease1 = await manager.get_or_create(
        key="a",
        factory=async_factory(calls),
        ttl_seconds=10,
    )

    lease2 = await manager.get_or_create(
        key="a",
        factory=async_factory(calls),
        ttl_seconds=10,
    )

    assert lease1 is lease2
    assert len(calls) == 1


@pytest.mark.asyncio
async def test_manager_creates_new_session_after_expiration():
    manager = SessionManager()
    created = []

    lease1 = await manager.get_or_create(
        key="a",
        factory=async_factory(created),
        ttl_seconds=1,
    )

    lease1._last_used_at -= 2

    lease2 = await manager.get_or_create(
        key="a",
        factory=async_factory(created),
        ttl_seconds=1,
    )

    assert lease1 is not lease2
    assert len(created) == 2


@pytest.mark.asyncio
async def test_manager_calls_on_close_on_expiration():
    manager = SessionManager()
    closed = []

    lease = await manager.get_or_create(
        key="a",
        factory=async_factory(),
        ttl_seconds=1,
        on_close=async_on_close(closed),
    )

    lease._last_used_at -= 2

    await manager.get_or_create(
        key="a",
        factory=async_factory(),
        ttl_seconds=1,
        on_close=async_on_close(closed),
    )

    assert len(closed) == 1
