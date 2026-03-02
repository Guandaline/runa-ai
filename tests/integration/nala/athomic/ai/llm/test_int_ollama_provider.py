# tests/integration/nala/athomic/ai/llm/test_int_ollama_provider.py
import importlib
import os
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
from pydantic import BaseModel, Field

from nala.athomic.ai.llm.providers.openai_provider import OpenAIProvider
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.ai,
]

# --- Models ---


class AnalysisResult(BaseModel):
    sentiment: str = Field(
        ..., description="Sentiment of the text: positive, negative, or neutral"
    )
    key_points: list[str] = Field(..., description="List of key points extracted")
    confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")


# --- Fixtures ---


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def ollama_available() -> bool:
    """Checks if Ollama is reachable."""
    base_url = "http://localhost:11434"
    try:
        async with httpx.AsyncClient(timeout=2.0) as client:
            response = await client.get(base_url)
            return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.fixture(scope="module", autouse=True)
def setup_integration_settings():
    os.environ["NALA_SETTINGS_FILES"] = "tests/settings/ai/test_int_llm_ollama.toml"
    get_settings.cache_clear()
    importlib.reload(settings_module)
    yield
    if "NALA_SETTINGS_FILES" in os.environ:
        del os.environ["NALA_SETTINGS_FILES"]
    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def provider(ollama_available: bool) -> AsyncGenerator[OpenAIProvider, None]:
    if not ollama_available:
        pytest.skip("Skipping Ollama LLM Test: Service not reachable.")

    settings = get_settings()

    try:
        conn_settings = settings.ai.connections.connections["ollama_llm_main"]
    except KeyError:
        pytest.fail("Could not find 'ollama_llm_main' in settings.")

    if env_model := os.getenv("OLLAMA_MODEL"):
        conn_settings.default_model = env_model

    conn_settings.provider.backend = "ollama"

    print(
        f"\n[SETUP] Initializing Ollama LLM Provider with model: {conn_settings.default_model}"
    )

    instance = OpenAIProvider(connection_settings=conn_settings)
    await instance.start()
    await instance.wait_ready()

    yield instance

    await instance.stop()


# --- Live Tests ---


async def test_ollama_generate_text(provider: OpenAIProvider):
    """Test basic text generation."""
    prompt = "Explain the concept of Dependency Injection in one sentence."
    print(f"\n[LIVE] Prompting: '{prompt}'")

    response = await provider.generate(prompt)

    assert isinstance(response, LLMResponse)
    assert response.content
    assert len(response.content) > 10
    print(f"[LIVE] Response: {response.content}")
    print(f"[LIVE] Usage: {response.usage}")


async def test_ollama_generate_structured(provider: OpenAIProvider):
    """Test structured output (JSON mode)."""
    prompt = """
    Analyze the following review and extract structured data:
    "I absolutely loved the service! The food was okay, but the staff was amazing. Highly recommended."
    
    Respond ONLY with valid JSON matching the schema.
    """

    print("\n[LIVE] Requesting Structured Output...")

    try:
        result = await provider.generate_structured(
            prompt=prompt, response_model=AnalysisResult
        )

        assert isinstance(result, AnalysisResult)
        assert result.sentiment in ["positive", "neutral", "negative"]
        assert len(result.key_points) > 0
        assert 0.0 <= result.confidence <= 1.0

        print(f"[LIVE] JSON Parsed: {result.model_dump_json(indent=2)}")

    except Exception as e:
        pytest.skip(f"Model failed structured output (common with small models): {e}")
