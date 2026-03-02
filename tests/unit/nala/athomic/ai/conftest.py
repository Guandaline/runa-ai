# tests/unit/ai/conftest.py
from unittest.mock import AsyncMock

import pytest
from pydantic import BaseModel, SecretStr

from nala.athomic.ai.governance.guards.protocol import AIGuardProtocol
from nala.athomic.config.schemas.ai.llm import (
    GoogleGenAIProviderSettings,
    LLMConnectionSettings,
    OpenAIProviderSettings,
)


class MockResponseModel(BaseModel):
    summary: str
    sentiment: str


@pytest.fixture
def mock_guard():
    guard = AsyncMock(spec=AIGuardProtocol)
    guard.check.return_value = None
    return guard


@pytest.fixture
def openai_settings():
    return LLMConnectionSettings(
        enabled=True,
        backend="openai",
        default_model="gpt-4",
        max_retries=1,
        timeout=10.0,
        provider=OpenAIProviderSettings(
            api_key=SecretStr("sk-test-123"), organization_id="org-test"
        ),
    )


@pytest.fixture
def vertex_settings():
    return LLMConnectionSettings(
        enabled=True,
        backend="vertex",
        default_model="gemini-pro",
        max_retries=1,
        timeout=10.0,
        provider=GoogleGenAIProviderSettings(
            project_id="test-project", location="us-central1"
        ),
    )


@pytest.fixture
def openai_embedding_settings():
    return LLMConnectionSettings(
        enabled=True,
        backend="openai",
        default_model="text-embedding-3-small",
        provider=OpenAIProviderSettings(
            api_key=SecretStr("sk-test-embed"), organization_id="org-test"
        ),
    )


@pytest.fixture
def vertex_embedding_settings():
    return LLMConnectionSettings(
        enabled=True,
        backend="vertex",
        default_model="text-embedding-004",
        provider=GoogleGenAIProviderSettings(
            project_id="test-project", location="us-central1"
        ),
    )
