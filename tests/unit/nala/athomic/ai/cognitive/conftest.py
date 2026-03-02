# tests/unit/nala/athomic/ai/cognitive/conftest.py
from unittest.mock import AsyncMock, MagicMock

import pytest

from nala.athomic.ai.llm.protocol import LLMProviderProtocol
from nala.athomic.ai.prompts.service import PromptService
from nala.athomic.config.schemas.ai.cognitive.cognitive_settings import (
    CognitiveSettings,
)


@pytest.fixture
def cognitive_settings():
    return CognitiveSettings(
        enabled=True,
        strategy="llm",
        default_model="gpt-4-turbo",
        confidence_threshold=0.8,
        default_prompt_template="cognitive/intent_classification",
    )


@pytest.fixture
def mock_llm_provider():
    llm = MagicMock(spec=LLMProviderProtocol)
    llm.generate_structured = AsyncMock()
    llm.wait_ready = AsyncMock()
    return llm


@pytest.fixture
def mock_prompt_service():
    service = MagicMock(spec=PromptService)
    service.render = MagicMock(return_value="Rendered Prompt")
    return service
