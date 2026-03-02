# tests/unit/nala/athomic/ai/cognitive/test_unit_factory.py
from unittest.mock import MagicMock, patch

import pytest

from nala.athomic.ai.cognitive.factory import CognitiveFactory
from nala.athomic.ai.cognitive.providers.llm import LLMCognitiveService
from nala.athomic.ai.cognitive.registry import cognitive_registry
from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)


@pytest.fixture
def mock_deps():
    with (
        patch("nala.athomic.ai.cognitive.factory.llm_manager") as llm_mgr,
        patch(
            "nala.athomic.ai.cognitive.factory.PromptServiceFactory"
        ) as prompt_factory,
    ):
        llm_mgr.get_client.return_value = MagicMock()
        prompt_factory.create.return_value = MagicMock()
        yield


def test_factory_creates_llm_service_by_default(mock_deps):
    # Arrange
    settings = CognitiveSettings(strategy="llm")

    # Act
    service = CognitiveFactory.create(settings)

    # Assert
    assert isinstance(service, LLMCognitiveService)
    assert service.settings.strategy == "llm"


def test_factory_resolves_global_settings_if_none_provided(mock_deps):
    # Arrange
    mock_app_settings = MagicMock()
    mock_app_settings.ai.cognitive = CognitiveSettings(strategy="llm")

    with patch(
        "nala.athomic.ai.cognitive.factory.get_settings", return_value=mock_app_settings
    ):
        service = CognitiveFactory.create()

        assert isinstance(service, LLMCognitiveService)


def test_factory_raises_error_on_unknown_strategy(mock_deps):
    # Arrange
    settings = CognitiveSettings(strategy="unknown_magic_strategy")

    # Act & Assert
    # The factory wraps registry errors in a RuntimeError
    with pytest.raises(RuntimeError, match="CognitiveService creation failed"):
        CognitiveFactory.create(settings)


def test_registry_has_defaults():
    # Verify standard registry state
    cls = cognitive_registry.get("llm")
    assert cls == LLMCognitiveService
