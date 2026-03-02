from unittest.mock import MagicMock, patch

import pytest

from nala.athomic.config.schemas.resilience.circuit_breaker import (
    CircuitBreakerSettings,
)
from nala.athomic.resilience.circuit_breaker.factory import CircuitBreakerFactory

SETTINGS_PATH = "nala.athomic.resilience.circuit_breaker.factory.get_settings"
SERVICE_PATH = "nala.athomic.resilience.circuit_breaker.factory.CircuitBreakerService"


class TestCircuitBreakerFactory:
    @pytest.fixture(autouse=True)
    def auto_clear_cache(self):
        CircuitBreakerFactory.clear_cache()
        yield
        CircuitBreakerFactory.clear_cache()

    @patch(SERVICE_PATH)
    @patch(SETTINGS_PATH)
    def test_create_returns_singleton_instance(
        self, mock_get_settings, mock_service_class
    ):
        instance1 = CircuitBreakerFactory.create()
        instance2 = CircuitBreakerFactory.create()

        assert instance1 is instance2
        mock_service_class.assert_called_once()

    @patch(SERVICE_PATH)
    @patch(SETTINGS_PATH)
    def test_clear_cache_allows_new_instance_creation(
        self, mock_get_settings, mock_service_class
    ):
        mock_service_class.side_effect = [
            MagicMock(name="instance1"),
            MagicMock(name="instance2"),
        ]

        instance1 = CircuitBreakerFactory.create()
        CircuitBreakerFactory.clear_cache()
        instance2 = CircuitBreakerFactory.create()

        assert instance1 is not instance2
        assert mock_service_class.call_count == 2

    @patch(SERVICE_PATH)
    @patch(SETTINGS_PATH)
    def test_create_uses_get_settings_when_none_is_provided(
        self, mock_get_settings, mock_service_class
    ):
        CircuitBreakerFactory.create(settings=None)
        mock_get_settings.assert_called_once()

    @patch(SERVICE_PATH)
    @patch(SETTINGS_PATH)
    def test_create_uses_provided_settings(self, mock_get_settings, mock_service_class):
        mock_custom_settings = MagicMock(spec=CircuitBreakerSettings)

        CircuitBreakerFactory.create(settings=mock_custom_settings)

        mock_get_settings.assert_not_called()
        mock_service_class.assert_called_once_with(settings=mock_custom_settings)
