from unittest.mock import AsyncMock, Mock, patch

import pytest

from nala.athomic.ai.prompts.service import PromptService
from nala.athomic.ai.prompts.types import PromptTemplate
from nala.athomic.config.schemas.ai.prompts import PromptSettings

# --- Fixtures ---


@pytest.fixture
def mock_settings():
    """Creates a default configuration object."""
    return PromptSettings(enabled=True, backend="filesystem", renderer="jinja2")


@pytest.fixture
def mock_loader():
    """Mocks the PromptLoaderProtocol."""
    loader = Mock()
    # Setup default behavior
    loader.get.return_value = PromptTemplate(
        name="test_prompt",
        version="1.0.0",
        template="Hello {{ name }}",
        input_variables=["name"],
    )
    # Add async lifecycle methods (optional in protocol but checked in service)
    loader.connect = AsyncMock()
    loader.close = AsyncMock()
    return loader


@pytest.fixture
def mock_renderer():
    """Mocks the PromptRendererProtocol."""
    renderer = Mock()
    renderer.render.return_value = "Hello Maō"
    return renderer


@pytest.fixture
def service(mock_settings, mock_loader, mock_renderer):
    """
    Initializes the PromptService with mocked internal components.
    We patch the Factories to return our mocks instead of real objects.
    """
    with (
        patch("nala.athomic.ai.prompts.service.PromptLoaderFactory") as loader_factory,
        patch(
            "nala.athomic.ai.prompts.service.PromptRendererFactory"
        ) as renderer_factory,
    ):
        loader_factory.create.return_value = mock_loader
        renderer_factory.create.return_value = mock_renderer

        svc = PromptService(settings=mock_settings)
        yield svc


# --- Tests ---


class TestPromptService:
    def test_initialization(self, service, mock_settings):
        """Should initialize correctly using the settings."""
        assert service.settings == mock_settings
        assert service.is_enabled() is True

    def test_get_template_delegation(self, service, mock_loader):
        """Should delegate template retrieval to the loader."""
        # Act
        result = service.get_template("my_prompt", version="1.2.3")

        # Assert
        mock_loader.get.assert_called_once_with("my_prompt", version="1.2.3")
        assert isinstance(result, PromptTemplate)
        assert result.name == "test_prompt"

    def test_render_flow(self, service, mock_loader, mock_renderer):
        """
        Should verify the full flow:
        1. Loader gets Template
        2. Renderer processes Template -> String
        """
        # Arrange
        variables = {"name": "Maō"}

        # Act
        result = service.render("my_prompt", variables, version=None)

        # Assert
        # 1. Check Loader call
        mock_loader.get.assert_called_once_with("my_prompt", version=None)

        # 2. Check Renderer call (must receive the template returned by loader)
        template_used = mock_loader.get.return_value
        mock_renderer.render.assert_called_once_with(template_used, variables)

        # 3. Check final result
        assert result == "Hello Maō"

    @pytest.mark.asyncio
    async def test_lifecycle_connect(self, service, mock_loader):
        """Should delegate connect() lifecycle to the loader if it has it."""
        # Act
        await service._connect()

        # Assert
        mock_loader.connect.assert_awaited_once()
        assert service.is_ready()

    @pytest.mark.asyncio
    async def test_lifecycle_close(self, service, mock_loader):
        """Should delegate close() lifecycle to the loader if it has it."""
        # Act
        await service._close()

        # Assert
        mock_loader.close.assert_awaited_once()
