# tests/unit/nala/athomic/ai/llm/providers/test_openai_provider.py
from unittest.mock import AsyncMock, MagicMock, patch

import openai
import pytest
from pydantic import ValidationError

from nala.athomic.ai.llm.exceptions import (
    AuthenticationError,
    ContextWindowExceededError,
    StructuredOutputError,
)
from nala.athomic.ai.llm.providers.openai_provider import OpenAIProvider
from nala.athomic.ai.schemas.llms import LLMResponse
from tests.unit.nala.athomic.ai.conftest import MockResponseModel


@pytest.fixture
def mock_openai_client():
    with patch("nala.athomic.ai.llm.providers.openai_provider.AsyncOpenAI") as mock:
        client_instance = AsyncMock(spec=openai.AsyncOpenAI)
        client_instance.__aenter__.return_value = client_instance
        client_instance.__aexit__.return_value = None
        mock.return_value = client_instance
        yield client_instance


@pytest.fixture
async def provider(openai_settings, mock_openai_client):
    """
    Async fixture to initialize the provider.
    Calls start() to ensure is_ready=True.
    """
    instance = OpenAIProvider(connection_settings=openai_settings)
    await instance.start()
    yield instance
    await instance.stop()


@pytest.mark.asyncio
async def test_openai_generate_content_success(provider, mock_openai_client):
    """Test successful text generation and response normalization."""
    mock_response = MagicMock()
    mock_response.model = "gpt-4"
    mock_response.choices[0].message.content = "Hello World"
    mock_response.choices[0].message.tool_calls = None
    mock_response.choices[0].finish_reason = "stop"

    mock_response.usage.prompt_tokens = 5
    mock_response.usage.completion_tokens = 10
    mock_response.usage.total_tokens = 15

    mock_openai_client.chat.completions.create = AsyncMock(return_value=mock_response)

    # Act
    result = await provider.generate("Hi")

    # Assert
    assert isinstance(result, LLMResponse)
    assert result.content == "Hello World"
    assert result.model == "gpt-4"
    assert result.usage.prompt_tokens == 5
    assert result.usage.total_tokens == 15

    mock_openai_client.chat.completions.create.assert_called_once()
    call_kwargs = mock_openai_client.chat.completions.create.call_args.kwargs
    assert call_kwargs["messages"][0]["content"] == "Hi"


@pytest.mark.asyncio
async def test_openai_auth_error_mapping(provider, mock_openai_client):
    """Test translation of OpenAI Auth Error."""
    mock_openai_client.chat.completions.create.side_effect = openai.AuthenticationError(
        "Invalid Key", response=MagicMock(), body=None
    )

    with pytest.raises(AuthenticationError, match="OpenAI authentication failed"):
        await provider.generate("Hi")


@pytest.mark.asyncio
async def test_openai_context_window_error_mapping(provider, mock_openai_client):
    """Test mapping of BadRequest to ContextWindowExceeded."""
    mock_openai_client.chat.completions.create.side_effect = openai.BadRequestError(
        "context_length_exceeded", response=MagicMock(), body=None
    )

    with pytest.raises(ContextWindowExceededError):
        await provider.generate("Huge prompt")


@pytest.mark.asyncio
async def test_openai_structured_validation_error(provider):
    """Test that instructor/pydantic validation errors become StructuredOutputError."""
    provider._client = AsyncMock()

    with patch("instructor.from_openai") as mock_instructor_factory:
        mock_client = AsyncMock()
        mock_client.chat.completions.create_with_completion.side_effect = (
            ValidationError.from_exception_data("Model", [])
        )

        mock_instructor_factory.return_value = mock_client

        with pytest.raises(StructuredOutputError):
            await provider.generate_structured("Extract", MockResponseModel)
