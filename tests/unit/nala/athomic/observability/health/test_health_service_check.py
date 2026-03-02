# Em: tests/unit/nala/athomic/observability/health/checks/test_service_check.py

from unittest.mock import MagicMock

import pytest

# The class we are testing
from nala.athomic.observability.health.checks.service_check import ServiceReadinessCheck

# The protocol our mock will simulate
from nala.athomic.services.protocol import BaseServiceProtocol


@pytest.fixture
def mock_service() -> MagicMock:
    """Creates a mock resembling a BaseService for the tests."""
    # The spec ensures the mock only has methods and attributes defined in the protocol
    service = MagicMock(spec=BaseServiceProtocol)
    service.service_name = "mocked_service"
    return service


@pytest.fixture
def service_check(mock_service: MagicMock) -> ServiceReadinessCheck:
    """Creates an instance of our ServiceReadinessCheck with the mocked service."""
    return ServiceReadinessCheck(service=mock_service)


class TestServiceReadinessCheck:
    """Test suite for the generic ServiceReadinessCheck."""

    def test_name_is_correctly_set_from_service(
        self, service_check: ServiceReadinessCheck, mock_service: MagicMock
    ):
        """Checks if the check name is the same as the service name."""
        # Arrange
        mock_service.service_name = "my_database_service"

        # Act
        # Recreate the instance so __init__ picks up the new name
        check = ServiceReadinessCheck(service=mock_service)

        # Assert
        assert check.name == "my_database_service"

    def test_enabled_when_service_is_enabled(
        self, service_check: ServiceReadinessCheck, mock_service: MagicMock
    ):
        """Checks if the check reports as enabled when the service is enabled."""
        # Arrange
        mock_service.is_enabled.return_value = True

        # Act & Assert
        assert service_check.enabled() is True
        mock_service.is_enabled.assert_called_once()

    def test_disabled_when_service_is_disabled(
        self, service_check: ServiceReadinessCheck, mock_service: MagicMock
    ):
        """Checks if the check reports as disabled when the service is disabled."""
        # Arrange
        mock_service.is_enabled.return_value = False

        # Act & Assert
        assert service_check.enabled() is False
        mock_service.is_enabled.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_returns_true_when_service_is_ready(
        self, service_check: ServiceReadinessCheck, mock_service: MagicMock
    ):
        """Checks if the check passes when the service is ready."""
        # Arrange
        mock_service.is_ready.return_value = True

        # Act
        result = await service_check.check()

        # Assert
        assert result is True
        mock_service.is_ready.assert_called_once()

    @pytest.mark.asyncio
    async def test_check_returns_false_when_service_is_not_ready(
        self, service_check: ServiceReadinessCheck, mock_service: MagicMock
    ):
        """Checks if the check fails when the service is not ready."""
        # Arrange
        mock_service.is_ready.return_value = False

        # Act
        result = await service_check.check()

        # Assert
        assert result is False
        mock_service.is_ready.assert_called_once()
