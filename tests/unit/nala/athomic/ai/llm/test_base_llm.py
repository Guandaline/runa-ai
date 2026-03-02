# tests/unit/nala/athomic/ai/llm/test_base_llm.py
from typing import Any, AsyncGenerator, List, Optional, Type
from unittest.mock import MagicMock, patch

import pytest
from pydantic import BaseModel

from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.schemas.llms import LLMResponse, LLMResponseChunk, TokenUsage
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.config.schemas.ai.llm.llm_settings import (
    GenerationSettings,
    LLMConnectionSettings,
    OpenAIProviderSettings,
)


class MockStructuredModel(BaseModel):
    summary: str
    sentiment: str


class DummyLLM(BaseLLM):
    """
    Concrete implementation of BaseLLM to test instrumentation and delegation
    of the base class.
    """

    async def _generate(
        self,
        _prompt: Optional[str] = None,
        _system_message: Optional[str] = None,
        _tools: Optional[List[AIToolProtocol]] = None,
        **_kwargs: Any,
    ) -> LLMResponse:
        """Mock of the real API call to the provider."""
        return LLMResponse(
            content="dummy_response",
            model="dummy-model",
            finish_reason="stop",
            usage=TokenUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        )

    async def _stream_generate(
        self,
        _prompt: Optional[str] = None,
        _system_message: Optional[str] = None,
        _tools: Optional[List[AIToolProtocol]] = None,
        **_kwargs: Any,
    ) -> AsyncGenerator[LLMResponseChunk, None]:
        """Mock of the streaming generation call."""
        yield LLMResponseChunk(content_delta="dummy_stream")

    async def _generate_structured(
        self,
        _prompt: str,
        _response_model: Type[Any],
        _system_message: Optional[str] = None,
        _max_retries: int = 3,
        **_kwargs: Any,
    ) -> Any:
        """Mock of structured generation call."""
        return MockStructuredModel(summary="test", sentiment="positive")


@pytest.fixture
def openai_settings():
    """Returns a valid settings object."""
    return LLMConnectionSettings(
        backend="openai",
        enabled=True,
        default_model="gpt-test",
        provider=OpenAIProviderSettings(
            api_key="sk-test",  # pragma: allowlist secret
            organization="org-test",
        ),
        generation=GenerationSettings(
            temperature=0.5,
            max_output_tokens=100,
        ),
    )


@pytest.mark.asyncio
async def test_generate_content_flow_instrumentation(openai_settings):
    """
    Verifies that BaseLLM.generate:
    1. Delegates to _generate.
    2. Records token metrics.
    """
    # Arrange
    provider = DummyLLM(connection_settings=openai_settings)
    await provider.start()

    with (
        patch("nala.athomic.ai.llm.base.llm_operations_total") as mock_ops_metric,
        patch("nala.athomic.ai.llm.base.llm_token_usage_total") as mock_tokens_metric,
    ):
        mock_ops_metric.labels.return_value = MagicMock(inc=MagicMock())
        mock_tokens_metric.labels.return_value = MagicMock(inc=MagicMock())

        # Act
        result = await provider.generate(prompt="hello")

        # Assert
        assert isinstance(result, LLMResponse)
        assert result.content == "dummy_response"

        mock_ops_metric.labels.assert_called()
        mock_tokens_metric.labels.assert_called()
        mock_tokens_metric.labels.return_value.inc.assert_any_call(10)  # Prompt tokens
        mock_tokens_metric.labels.return_value.inc.assert_any_call(
            20
        )  # Completion tokens


@pytest.mark.asyncio
async def test_generate_structured_flow_instrumentation(openai_settings):
    """
    Verifies that BaseLLM.generate_structured delegates correctly and returns the Pydantic object.
    """
    # Arrange
    provider = DummyLLM(connection_settings=openai_settings)
    await provider.start()

    # Act
    result = await provider.generate_structured(
        prompt="Summarize the test case", response_model=MockStructuredModel
    )

    # Assert
    assert isinstance(result, MockStructuredModel)
    assert result.summary == "test"
    assert result.sentiment == "positive"
