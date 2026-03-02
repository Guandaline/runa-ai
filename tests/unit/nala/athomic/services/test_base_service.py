# tests/unit/nala/athomic/services/test_base_service.py

import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.services.base import BaseService, ServiceState
from nala.athomic.services.exceptions import (
    ServiceAlreadyRunningError,
    ServiceConnectionError,
)


class DummyService(BaseService):
    """A minimal BaseService implementation for testing."""

    def __init__(self, service_name="dummy_service", enabled=True, loop_sleep=0.01):
        super().__init__(service_name=service_name, enabled=enabled)
        self._connect_was_called = False
        self._close_was_called = False
        self.loop_sleep = loop_sleep

    async def _connect(self) -> None:
        self._connect_was_called = True

    async def _close(self) -> None:
        self._close_was_called = True

    async def _run_loop(self) -> None:
        try:
            while True:
                await asyncio.sleep(self.loop_sleep)
        except asyncio.CancelledError:
            self.logger.info("DummyService loop correctly cancelled.")
            raise


@pytest.fixture
def dummy_service() -> DummyService:
    """Provides a fresh instance of DummyService for each test."""
    return DummyService()


@pytest.fixture
def mock_metrics():
    """Mocks all relevant metrics for the BaseService tests."""
    with (
        patch(
            "nala.athomic.services.base.service_connection_attempts_total"
        ) as attempts,
        patch(
            "nala.athomic.services.base.service_connection_failures_total"
        ) as failures,
        patch("nala.athomic.services.base.service_connection_status") as status,
        patch("nala.athomic.services.base.service_readiness_status") as readiness,
    ):
        yield {
            "attempts": attempts,
            "failures": failures,
            "status": status,
            "readiness": readiness,
        }


@pytest.mark.asyncio
class TestBaseServiceLifecycle:
    """Tests for the service lifecycle methods."""

    async def test_connect_success(self, dummy_service: DummyService, mock_metrics):
        """Ensures a successful connection flow sets the correct states."""
        await dummy_service.start()

        assert dummy_service.is_ready()
        assert dummy_service.is_running()
        assert dummy_service._state == ServiceState.READY
        mock_metrics["attempts"].labels(
            service="dummy_service"
        ).inc.assert_called_once()

    async def test_connect_failure_raises_service_connection_error(
        self, dummy_service: DummyService, mock_metrics, mocker
    ):
        """Ensures a connection failure raises a wrapped ServiceConnectionError."""
        mocker.patch.object(
            dummy_service,
            "_connect",
            new_callable=AsyncMock,
            side_effect=ValueError("DB Down"),
        )

        with pytest.raises(ServiceConnectionError):
            await dummy_service.start()

        assert not dummy_service.is_ready()
        assert dummy_service._state == ServiceState.FAILED
        mock_metrics["failures"].labels(
            service="dummy_service"
        ).inc.assert_called_once()

    async def test_connect_is_idempotent(self, dummy_service: DummyService):
        """Ensures that start() is only executed once even if called multiple times."""
        dummy_service._connect = AsyncMock()

        await asyncio.gather(
            dummy_service.start(),
            dummy_service.start(),
        )

        dummy_service._connect.assert_awaited_once()

    async def test_close_success(self, dummy_service: DummyService, mock_metrics):
        """Tests a clean shutdown of a running service."""
        await dummy_service.start()
        await dummy_service.close()

        assert not dummy_service.is_running()
        assert not dummy_service.is_ready()
        assert dummy_service._state == ServiceState.CLOSED
        assert dummy_service._close_was_called
        mock_metrics["readiness"].labels(
            service="dummy_service"
        ).set.assert_called_with(0)

    async def test_connect_after_close_raises_error(self, dummy_service: DummyService):
        """Ensures that a service cannot be re-started after being closed."""
        await dummy_service.start()
        await dummy_service.close()

        with pytest.raises(ServiceAlreadyRunningError):
            await dummy_service.start()

    async def test_wait_ready_waits_and_unblocks(self, dummy_service: DummyService):
        """Tests that wait_ready() blocks until the service is ready."""
        waiter_task = asyncio.create_task(dummy_service.wait_ready())

        await asyncio.sleep(0.01)
        assert not waiter_task.done()

        await dummy_service.start()
        await asyncio.sleep(0.01)

        assert waiter_task.done()
        await waiter_task

    async def test_concurrency_lock_prevents_race_conditions(
        self, dummy_service: DummyService
    ):
        """
        Tests that the internal lock prevents _connect from being called multiple
        times under concurrent access.
        """
        original_connect = dummy_service._connect

        async def slow_connect():
            await asyncio.sleep(0.05)
            await original_connect()

        dummy_service._connect = AsyncMock(side_effect=slow_connect)

        tasks = [asyncio.create_task(dummy_service.start()) for _ in range(5)]
        await asyncio.gather(*tasks)

        dummy_service._connect.assert_awaited_once()
