# tests/unit/nala/athomic/ai/cognitive/providers/test_unit_llm_service.py
from unittest.mock import patch

import pytest
from opentelemetry.trace import StatusCode

from nala.athomic.ai.cognitive.exceptions import IntentClassificationError
from nala.athomic.ai.cognitive.providers.llm import LLMCognitiveService
from nala.athomic.ai.schemas.cognitive import IntentClassification, UserIntent


@pytest.fixture
def llm_service(cognitive_settings, mock_llm_provider, mock_prompt_service):
    """
    Creates a service instance.
    Note: We don't call connect() here to allow manual lifecycle testing.
    """
    service = LLMCognitiveService(
        llm=mock_llm_provider,
        prompt_service=mock_prompt_service,
        settings=cognitive_settings,
    )
    return service


@pytest.mark.asyncio
async def test_lifecycle_connect(llm_service, mock_llm_provider):
    """Verifies that the service initializes correctly."""
    await llm_service.connect()

    mock_llm_provider.wait_ready.assert_awaited_once()
    assert llm_service.is_ready()


@pytest.mark.asyncio
async def test_classify_success_flow(
    llm_service, mock_llm_provider, mock_prompt_service
):
    """Test the happy path classification flow."""
    # 1. SETUP: Connect the service to avoid blocking on wait_ready
    await llm_service.connect()

    # Arrange
    expected_intent = IntentClassification(
        primary_intent=UserIntent.SEARCH,
        confidence=0.95,
        detected_entities=["invoice", "2024"],
        rewritten_query="search invoice 2024",
    )
    mock_llm_provider.generate_structured.return_value = expected_intent

    # Act
    with patch(
        "nala.athomic.ai.cognitive.base.cognitive_classification_total"
    ) as mock_metric:
        result = await llm_service.classify(
            query="Find invoice from 2024", history_context="previous chat"
        )

        # Assert Result
        assert result == expected_intent
        assert result.primary_intent == UserIntent.SEARCH

        # Assert Logic Delegation
        mock_prompt_service.render.assert_called_once()
        mock_llm_provider.generate_structured.assert_awaited_once()

        call_kwargs = mock_llm_provider.generate_structured.call_args.kwargs
        assert call_kwargs["response_model"] == IntentClassification
        assert call_kwargs["temperature"] == pytest.approx(0.0)

        # Assert Telemetry (Base Class Logic)
        mock_metric.labels.assert_called_with(
            provider="cognitive_service_llm", strategy="llm", status="success"
        )
        mock_metric.labels.return_value.inc.assert_called_once()


@pytest.mark.asyncio
async def test_classify_handles_llm_error(llm_service, mock_llm_provider):
    """Test LLM error handling."""
    # 1. SETUP
    await llm_service.connect()

    # Arrange
    mock_llm_provider.generate_structured.side_effect = Exception("LLM Down")

    # Act
    with patch(
        "nala.athomic.ai.cognitive.base.cognitive_classification_total"
    ) as mock_metric:
        with pytest.raises(IntentClassificationError) as exc:
            await llm_service.classify("query")

        assert "LLM Classification failed" in str(exc.value)

        # Assert Failure Metric
        mock_metric.labels.assert_called_with(
            provider="cognitive_service_llm", strategy="llm", status="failure"
        )


@pytest.mark.asyncio
async def test_classify_observability_tracing(llm_service, mock_llm_provider):
    """Test trace spans."""
    # 1. SETUP
    await llm_service.connect()

    # Arrange
    mock_llm_provider.generate_structured.return_value = IntentClassification(
        primary_intent=UserIntent.ASK, confidence=1.0, detected_entities=[]
    )

    # Act
    # We inspect the tracer provided by BaseService
    with patch.object(llm_service.tracer, "start_as_current_span") as mock_span_ctx:
        mock_span = mock_span_ctx.return_value.__enter__.return_value

        await llm_service.classify("hello")

        # Assert Attributes Set
        assert mock_span.set_attribute.called
        mock_span.set_status.assert_called_with(StatusCode.OK)
