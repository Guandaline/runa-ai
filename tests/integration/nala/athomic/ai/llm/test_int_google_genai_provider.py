# tests/integration/nala/athomic/ai/llm/test_int_google_genai_provider.py
import importlib
import os
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from pydantic import BaseModel, Field

from nala.athomic.ai.llm.providers.google_genai_provider import GoogleGenAIProvider
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.ai,
]


class CityFacts(BaseModel):
    """Model to test structured output capabilities."""

    city_name: str = Field(..., description="The name of the city.")
    country: str = Field(..., description="The country the city is in.")
    population_estimate: int = Field(..., description="Estimated population.")
    fun_fact: str = Field(..., description="A short fun fact about the city.")


@pytest.fixture(scope="module")
def gcp_credentials_present() -> bool:
    """Checks if GCP credentials are available in the environment."""
    project_id = (
        os.getenv("NALA_TEST_GCP_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
    )

    # Check for ADC credentials file or explicit env var
    has_adc = os.path.exists(
        os.path.expanduser("~/.config/gcloud/application_default_credentials.json")
    )
    env_creds = os.getenv("GOOGLE_APPLICATION_CREDENTIALS")

    return bool(project_id and (has_adc or env_creds))


@pytest.fixture(scope="module", autouse=True)
def setup_integration_settings(gcp_credentials_present):
    """
    Sets up settings once for the whole module.
    """
    if not gcp_credentials_present:
        pytest.skip("Skipping Google GenAI Integration Test: No GCP credentials found.")

    # Define environment variable for the module scope
    os.environ["NALA_SETTINGS_FILES"] = "tests/settings/ai/test_int_google_genai.toml"

    get_settings.cache_clear()
    importlib.reload(settings_module)

    yield

    # Cleanup after all tests in module are done
    if "NALA_SETTINGS_FILES" in os.environ:
        del os.environ["NALA_SETTINGS_FILES"]
    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="module", loop_scope="module")
async def provider() -> AsyncGenerator[GoogleGenAIProvider, None]:
    """
    Creates and connects the GoogleGenAIProvider ONCE for all tests.
    This drastically reduces test time by reusing the authenticated session.
    """
    settings = get_settings()

    try:
        conn_settings = settings.ai.connections.connections["genai_main"]
    except KeyError:
        pytest.fail("Could not find 'genai_main' connection in settings.")

    real_project_id = (
        os.getenv("NALA_TEST_GCP_PROJECT_ID")
        or os.getenv("GOOGLE_CLOUD_PROJECT")
        or os.getenv("GCP_PROJECT_ID")
    )
    real_location = (
        os.getenv("NALA_TEST_GCP_LOCATION")
        or os.getenv("GOOGLE_CLOUD_LOCATION")
        or "us-central1"
    )
    real_model = os.getenv("MODEL_ID", "gemini-1.5-flash")

    if not real_project_id:
        pytest.fail("Project ID env var is missing during provider setup.")

    conn_settings.provider.project_id = real_project_id
    conn_settings.provider.location = real_location
    conn_settings.default_model = real_model

    print(
        f"\n[SETUP] Initializing Provider with: Project={real_project_id}, Location={real_location}, Model={real_model}"
    )

    instance = GoogleGenAIProvider(connection_settings=conn_settings)

    await instance.start()
    await instance.wait_ready()

    yield instance

    await instance.stop()


# --- Live Tests ---


async def test_live_text_generation(provider: GoogleGenAIProvider):
    """Verifies basic connectivity and text generation with Vertex AI."""
    print("\n[LIVE] Generating text...")

    prompt = "Reply with exactly the word 'Pong'."

    response = await provider.generate(prompt)

    assert isinstance(response, LLMResponse)
    assert response.content is not None

    clean_content = response.content.strip().lower()
    clean_content = clean_content.replace(".", "")

    assert "pong" in clean_content
    assert response.usage.total_tokens > 0
    print(f"[LIVE] Success. Response: {response.content}")


async def test_live_structured_output(provider: GoogleGenAIProvider):
    """Verifies the native structured output (JSON mode) of Gemini."""
    print("\n[LIVE] Testing Structured Output...")

    prompt = "Give me facts about Tokyo, Japan."

    result = await provider.generate_structured(
        prompt=prompt, response_model=CityFacts, max_retries=1
    )

    assert isinstance(result, CityFacts)
    assert result.city_name == "Tokyo"
    assert result.country == "Japan"
    assert result.population_estimate > 1_000_000

    print(f"[LIVE] Success. Parsed Object: {result.model_dump_json(indent=2)}")
