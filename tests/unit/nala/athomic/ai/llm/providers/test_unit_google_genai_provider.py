# tests/unit/nala/athomic/ai/llm/providers/test_unit_google_genai_provider.py
from http import HTTPStatus
from typing import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from pydantic import BaseModel, SecretStr

from nala.athomic.ai.llm.exceptions import (
    AuthenticationError,
    ContextWindowExceededError,
    RateLimitError,
    StructuredOutputError,
)
from nala.athomic.ai.llm.providers.google_genai_provider import GoogleGenAIProvider
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config.schemas.ai import (
    GenerationSettings,
    GoogleGenAIProviderSettings,
    LLMConnectionSettings,
)

# --- Fixtures ---


@pytest.fixture
def genai_settings() -> LLMConnectionSettings:
    """Creates a valid configuration for Vertex AI mode."""
    return LLMConnectionSettings(
        backend="google_genai",
        default_model="gemini-1.5-pro",
        generation=GenerationSettings(
            temperature=0.3,
            max_output_tokens=512,
        ),
        provider=GoogleGenAIProviderSettings(
            project_id="test-project",
            location="us-central1",
            backend="google_genai",
        ),
    )


@pytest.fixture
def mock_genai_client():
    """Mocks the google.genai.Client and its nested aio.models structure."""
    with patch(
        "nala.athomic.ai.llm.providers.google_genai_provider.genai.Client"
    ) as mock_cls:
        client_instance = MagicMock()

        # Mock the async model interface: client.aio.models.generate_content
        client_instance.aio = MagicMock()
        client_instance.aio.models = MagicMock()
        client_instance.aio.models.generate_content = AsyncMock()

        mock_cls.return_value = client_instance
        yield mock_cls, client_instance


@pytest.fixture
async def provider(
    genai_settings, mock_genai_client
) -> AsyncGenerator[GoogleGenAIProvider, None]:
    provider = GoogleGenAIProvider(genai_settings)
    await provider.connect()
    yield provider


# --- Helper Models ---


class WeatherInfo(BaseModel):
    city: str
    temperature: float


# --- Tests ---


@pytest.mark.asyncio
async def test_connect_initializes_vertex_mode(genai_settings, mock_genai_client):
    """Verifies that the client is initialized with vertexai=True when project_id is present."""
    mock_cls, _ = mock_genai_client

    provider = GoogleGenAIProvider(genai_settings)
    await provider.connect()

    mock_cls.assert_called_once_with(
        vertexai=True,
        project="test-project",
        location="us-central1",
        api_key=None,
    )


@pytest.mark.asyncio
async def test_connect_initializes_studio_mode(mock_genai_client):
    """Verifies that the client is initialized with vertexai=False when using API Key."""
    mock_cls, _ = mock_genai_client

    settings = LLMConnectionSettings(
        backend="google_genai",
        default_model="gemini-1.5-flash",
        provider=GoogleGenAIProviderSettings(
            api_key=SecretStr("fake-key"), backend="google_genai"
        ),
    )

    provider = GoogleGenAIProvider(settings)
    await provider.connect()

    mock_cls.assert_called_once_with(
        vertexai=False,
        project=None,
        location=None,
        api_key="fake-key",  # pragma: allowlist secret
    )


@pytest.mark.asyncio
async def test_generate_success(provider, mock_genai_client):
    """Tests successful text generation and response parsing."""
    _, client_instance = mock_genai_client

    # Mock Response Structure
    mock_response = MagicMock()

    # Candidate Content
    mock_candidate = MagicMock()
    mock_part = MagicMock()
    mock_part.text = "Hello, Nala!"
    mock_part.function_call = None
    mock_candidate.content.parts = [mock_part]
    mock_candidate.finish_reason.name = "STOP"

    mock_response.candidates = [mock_candidate]

    # Usage Metadata
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 5
    mock_response.usage_metadata.total_token_count = 15

    client_instance.aio.models.generate_content.return_value = mock_response

    # Act
    response = await provider.generate("Hi")

    # Assert
    assert isinstance(response, LLMResponse)
    assert response.content == "Hello, Nala!"
    assert response.finish_reason == "STOP"
    assert response.usage.total_tokens == 15

    # Verify call arguments
    client_instance.aio.models.generate_content.assert_awaited_once()
    call_kwargs = client_instance.aio.models.generate_content.call_args.kwargs
    assert call_kwargs["model"] == "gemini-1.5-pro"
    assert call_kwargs["contents"] == "Hi"

    # Verify Config
    config = call_kwargs["config"]
    assert config.temperature == pytest.approx(0.3)
    assert config.max_output_tokens == 512


@pytest.mark.asyncio
async def test_generate_tool_calls(provider, mock_genai_client):
    """Tests parsing of function calls from the response."""
    _, client_instance = mock_genai_client

    # Mock Response with Function Call
    mock_response = MagicMock()
    mock_candidate = MagicMock()

    mock_part = MagicMock()
    mock_part.text = None
    mock_part.function_call.name = "get_weather"
    mock_part.function_call.args = {"city": "Florianópolis"}

    mock_candidate.content.parts = [mock_part]
    mock_candidate.finish_reason.name = "STOP"

    mock_response.candidates = [mock_candidate]
    mock_response.usage_metadata = None

    client_instance.aio.models.generate_content.return_value = mock_response

    # Act
    response = await provider.generate("Weather in Floripa")

    # Assert
    assert response.has_tool_calls
    tool_call = response.tool_calls[0]
    assert tool_call.name == "get_weather"
    assert tool_call.arguments["city"] == "Florianópolis"
    assert tool_call.id.startswith("call_get_weather_")


@pytest.mark.asyncio
async def test_generate_structured_success(provider, mock_genai_client):
    """Tests native structured output generation."""
    _, client_instance = mock_genai_client

    mock_response = MagicMock()
    mock_response.text = '{"city": "Tokyo", "temperature": 22.5}'
    mock_response.usage_metadata.prompt_token_count = 10
    mock_response.usage_metadata.candidates_token_count = 10

    client_instance.aio.models.generate_content.return_value = mock_response

    # Act
    result = await provider.generate_structured(
        "Current weather in Tokyo", response_model=WeatherInfo
    )

    # Assert
    assert isinstance(result, WeatherInfo)
    assert result.city == "Tokyo"
    assert result.temperature == pytest.approx(22.5)

    # Verify Config passed schema
    client_instance.aio.models.generate_content.assert_awaited_once()
    config = client_instance.aio.models.generate_content.call_args.kwargs["config"]
    assert config.response_mime_type == "application/json"
    assert config.response_schema is not None


@pytest.mark.asyncio
async def test_generate_structured_parsing_error(provider, mock_genai_client):
    """Tests handling of invalid JSON in structured output."""
    _, client_instance = mock_genai_client

    mock_response = MagicMock()
    mock_response.text = '{"city": "Tokyo", "invalid_json...'  # Malformed
    mock_response.usage_metadata = None

    client_instance.aio.models.generate_content.return_value = mock_response

    with pytest.raises(StructuredOutputError) as exc:
        await provider.generate_structured("prompt", WeatherInfo)

    assert "Failed to parse" in str(exc.value)


@pytest.mark.asyncio
async def test_error_handling_mapping(provider, mock_genai_client):
    """Tests mapping of HTTPStatus codes to Athomic exceptions."""
    _, client_instance = mock_genai_client

    with patch(
        "nala.athomic.ai.llm.providers.google_genai_provider.errors"
    ) as mock_errors_module:

        class MockClientError(Exception):
            def __init__(self, message, code=None):
                super().__init__(message)
                self.code = code

        mock_errors_module.ClientError = MockClientError

        # Case 1: Rate Limit (429)
        client_instance.aio.models.generate_content.side_effect = MockClientError(
            "Quota exceeded", HTTPStatus.TOO_MANY_REQUESTS
        )
        with pytest.raises(RateLimitError):
            await provider.generate("prompt")

        # Case 2: Auth Error (401)
        client_instance.aio.models.generate_content.side_effect = MockClientError(
            "Invalid API Key", HTTPStatus.UNAUTHORIZED
        )
        with pytest.raises(AuthenticationError):
            await provider.generate("prompt")

        # Case 3: Context Window (400 + message analysis)
        client_instance.aio.models.generate_content.side_effect = MockClientError(
            "Request contains too many tokens (context length)", HTTPStatus.BAD_REQUEST
        )
        with pytest.raises(ContextWindowExceededError):
            await provider.generate("huge prompt")
