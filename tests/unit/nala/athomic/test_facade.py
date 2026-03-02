# tests/unit/nala/athomic/test_facade.py
from unittest.mock import AsyncMock, patch

import pytest

from nala.athomic.facade import Athomic

# Paths to the modules we will now mock
GET_SETTINGS_PATH = "nala.athomic.facade.get_settings"
LIFECYCLE_MANAGER_PATH = "nala.athomic.facade.LifecycleManager"
REGISTER_SERVICES_PATH = "nala.athomic.facade.register_athomic_infra_services"


@pytest.fixture
def mock_dependencies():
    """Fixture to mock all dependencies of the Athomic Facade."""
    with (
        patch(GET_SETTINGS_PATH) as mock_get_settings,
        patch(LIFECYCLE_MANAGER_PATH) as mock_lifecycle_manager_cls,
        patch(REGISTER_SERVICES_PATH) as mock_register_services,
    ):
        # Configure mocks for the instances
        mock_sp_instance = AsyncMock(name="SecretsProviderInstance")
        mock_lm_instance = AsyncMock(name="LifecycleManagerInstance")

        # Mock the .create() classmethods
        mock_lifecycle_manager_cls.return_value = mock_lm_instance

        yield {
            "get_settings": mock_get_settings,
            "lifecycle_manager_cls": mock_lifecycle_manager_cls,
            "register_services": mock_register_services,
            "sp_instance": mock_sp_instance,
            "lm_instance": mock_lm_instance,
        }


class TestAthomicFacade:
    """Test suite for the Athomic Facade."""

    def test_init_creates_dependencies(self, mock_dependencies):
        """
        Tests if the Athomic Facade constructor correctly instantiates
        its managers by calling the appropriate factories and registration functions.
        """
        # Arrange
        mock_settings = mock_dependencies["get_settings"].return_value

        # Act
        athomic = Athomic()

        # Assert
        # 1. It should call the service registration function
        mock_dependencies["register_services"].assert_called_once_with(
            settings=mock_settings
        )

        # 5. It should instantiate LifecycleManager
        mock_dependencies["lifecycle_manager_cls"].assert_called_once_with(
            settings=mock_settings,
            domain_initializers_register=None,
        )
        assert athomic.lifecycle_manager is mock_dependencies["lm_instance"]

    @pytest.mark.asyncio
    async def test_shutdown_sequence(self, mock_dependencies):
        """
        Checks if the shutdown method correctly calls the shutdown of LifecycleManager.
        """
        # Arrange
        athomic = Athomic()
        lm_instance = athomic.lifecycle_manager

        # Act
        await athomic.shutdown()

        # Assert
        lm_instance.shutdown.assert_awaited_once()
