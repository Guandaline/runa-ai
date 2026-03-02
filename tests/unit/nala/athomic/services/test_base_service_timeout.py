import asyncio
import time
from typing import AsyncGenerator
from unittest.mock import AsyncMock

import pytest

from nala.athomic.services.base import BaseService
from nala.athomic.services.enums import ServiceState


class DummyService(BaseService):
    """A dummy service for testing that simulates a long-running task."""

    def __init__(self, service_name: str, connect_delay: float = 0.01):
        super().__init__(service_name=service_name)
        self._connect_delay = connect_delay

    async def _connect(self) -> None:
        """Just a placeholder for connect logic."""
        await asyncio.sleep(self._connect_delay)

    async def _close(self) -> None:
        """Just a placeholder for close logic."""
        pass

    async def _run_loop(self):
        try:
            while True:
                await asyncio.sleep(1)
        except asyncio.CancelledError:
            self.logger.info("DummyService loop correctly cancelled.")
            raise


@pytest.fixture
async def dummy_service(request) -> AsyncGenerator[DummyService, None]:
    """
    Fixture that manages the full lifecycle of a DummyService for each test.
    Uses 'request.param' to allow passing arguments to the fixture.
    """
    params = getattr(request, "param", {})
    service_name = params.get("service_name", "dummy")
    connect_delay = params.get("connect_delay", 0.01)

    service = DummyService(service_name=service_name, connect_delay=connect_delay)
    try:
        yield service
    finally:
        if service.is_running():
            await service.stop()


@pytest.mark.asyncio
async def test_idempotent_connect_and_close(dummy_service: DummyService):
    await dummy_service.connect()
    assert dummy_service.is_connected()

    await dummy_service.connect()
    assert dummy_service.is_connected()

    await dummy_service.stop()
    assert not dummy_service.is_connected()
    assert dummy_service.is_closed()

    await dummy_service.stop()
    assert not dummy_service.is_connected()


@pytest.mark.asyncio
async def test_health_info(dummy_service: DummyService):
    """Tests if the health() method returns the correct service state."""
    h_before = dummy_service.health()
    assert h_before["connected"] is False
    assert h_before["ready"] is False
    assert h_before["state"] == "PENDING"

    await dummy_service.start()
    await dummy_service.wait_ready()

    h_after = dummy_service.health()
    assert isinstance(h_after, dict)
    assert h_after["service_name"] == "dummy"
    assert h_after["connected"] is True
    assert h_after["ready"] is True
    assert h_after["running"] is True
    assert h_after["state"] == "READY"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dummy_service",
    [{"service_name": "dummy_slow", "connect_delay": 0.2}],
    indirect=True,
)
async def test_connection_timeout(dummy_service: DummyService):
    """
    Tests if a caller can enforce a timeout on a service that takes too long to connect.
    """
    # Arrange
    start_time = time.monotonic()

    # Act & Assert
    with pytest.raises(asyncio.TimeoutError):
        await asyncio.wait_for(dummy_service.connect(), timeout=0.1)

    end_time = time.monotonic()
    duration = end_time - start_time

    assert 0.1 <= duration < 0.2
    assert not dummy_service.is_connected()
    assert dummy_service._state == ServiceState.CONNECTING


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "dummy_service", [{"service_name": "test_state_service"}], indirect=True
)
async def test_base_service_state_is_ready_after_connect(
    dummy_service: DummyService, mocker
):
    """
    Diagnostic: Tests if the service state is READY after connect.
    """
    mocker.patch.object(dummy_service, "_connect", new_callable=AsyncMock)

    try:
        await dummy_service.start()
        await dummy_service.wait_ready()

        assert dummy_service.is_ready() is True
        assert dummy_service._state == ServiceState.READY
    finally:
        await dummy_service.stop()
