# tests/unit/nala/athomic/resilience/circuit_breaker/test_cb_service.py
from datetime import timedelta
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.config.schemas.resilience.circuit_breaker import (
    CircuitBreakerSettings,
    CircuitSpecificSettings,
)
from nala.athomic.resilience.circuit_breaker.listeners import global_logging_listener
from nala.athomic.resilience.circuit_breaker.service import CircuitBreakerService

STORAGE_FACTORY_PATH = (
    "nala.athomic.resilience.circuit_breaker.service.CircuitBreakerStorageFactory"
)
AIOBREAKER_PATH = (
    "nala.athomic.resilience.circuit_breaker.service.aiobreaker.CircuitBreaker"
)


@pytest.mark.asyncio
class TestCircuitBreakerService:
    @pytest.fixture
    def settings_default(self) -> CircuitBreakerSettings:
        return CircuitBreakerSettings(default_fail_max=5, default_reset_timeout_sec=30)

    @pytest.fixture
    def settings_specific(self) -> CircuitBreakerSettings:
        return CircuitBreakerSettings(
            default_fail_max=5,
            default_reset_timeout_sec=30,
            circuits={
                "my_special_circuit": CircuitSpecificSettings(
                    fail_max=2, reset_timeout_sec=10
                )
            },
        )

    @patch(AIOBREAKER_PATH)
    @patch(STORAGE_FACTORY_PATH, new_callable=AsyncMock)
    async def test_creates_breaker_with_default_settings(
        self, mock_storage_factory, mock_aiobreaker, settings_default
    ):
        service = CircuitBreakerService(settings=settings_default)
        mock_storage_factory.create.return_value = AsyncMock()

        await service._get_or_create_breaker("some_circuit")

        mock_storage_factory.create.assert_awaited_once_with(
            circuit_name="some_circuit", settings=settings_default
        )
        mock_aiobreaker.assert_called_once()

    @patch(AIOBREAKER_PATH)
    @patch(STORAGE_FACTORY_PATH, new_callable=AsyncMock)
    async def test_creates_breaker_with_specific_settings(
        self, mock_storage_factory, mock_aiobreaker, settings_specific
    ):
        service = CircuitBreakerService(settings=settings_specific)
        mock_storage_factory.create.return_value = AsyncMock()

        await service._get_or_create_breaker("my_special_circuit")

        mock_storage_factory.create.assert_awaited_once_with(
            circuit_name="my_special_circuit", settings=settings_specific
        )
        mock_aiobreaker.assert_called_once_with(
            fail_max=2,
            timeout_duration=timedelta(seconds=10),
            state_storage=mock_storage_factory.create.return_value,
            listeners=[global_logging_listener],
            name="my_special_circuit",
        )

    @patch(AIOBREAKER_PATH)
    @patch(STORAGE_FACTORY_PATH, new_callable=AsyncMock)
    async def test_uses_cached_breaker_on_second_call(
        self, mock_storage_factory, mock_aiobreaker, settings_default
    ):
        service = CircuitBreakerService(settings=settings_default)
        mock_storage_factory.create.return_value = AsyncMock()

        await service._get_or_create_breaker("cached_circuit")
        await service._get_or_create_breaker("cached_circuit")

        mock_storage_factory.create.assert_awaited_once()
        mock_aiobreaker.assert_called_once()
