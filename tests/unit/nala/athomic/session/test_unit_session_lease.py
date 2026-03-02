import time

import pytest

from nala.athomic.session.lease import SessionLease
from tests.helpers import async_on_close


@pytest.mark.asyncio
async def test_lease_initial_state():
    resource = object()
    lease = SessionLease(resource, ttl_seconds=10)

    now = time.monotonic()

    assert lease.resource is resource
    assert lease.created_at <= now
    assert lease.last_used_at <= now
    assert lease.is_expired(now) is False


@pytest.mark.asyncio
async def test_lease_touch_updates_last_used():
    resource = object()
    lease = SessionLease(resource, ttl_seconds=10)

    first = lease.last_used_at
    lease.touch()
    second = lease.last_used_at

    assert second >= first


@pytest.mark.asyncio
async def test_lease_expires_after_ttl():
    resource = object()
    lease = SessionLease(resource, ttl_seconds=1)

    expired_at = lease.last_used_at + 2
    assert lease.is_expired(expired_at) is True


@pytest.mark.asyncio
async def test_lease_close_is_idempotent():
    closed = []

    lease = SessionLease(
        object(),
        ttl_seconds=10,
        on_close=async_on_close(closed),
    )

    await lease.close()
    await lease.close()

    assert len(closed) == 1


@pytest.mark.asyncio
async def test_lease_close_without_callback_is_safe():
    lease = SessionLease(object(), ttl_seconds=10)

    await lease.close()
    await lease.close()
