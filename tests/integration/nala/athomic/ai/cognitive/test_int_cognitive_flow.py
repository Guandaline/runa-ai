import importlib
from pathlib import Path
from typing import AsyncGenerator

import httpx
import pytest
import pytest_asyncio
import yaml

from nala.athomic.ai.cognitive.base import CognitiveBaseService
from nala.athomic.ai.cognitive.factory import CognitiveFactory
from nala.athomic.ai.llm.manager import llm_manager
from nala.athomic.ai.schemas.cognitive import UserIntent
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module
from nala.athomic.services.base import BaseService

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.ai,
]


async def check_ollama_health(base_url: str = "http://localhost:11434") -> bool:
    """Helper to check if Ollama is reachable."""
    try:
        async with httpx.AsyncClient(timeout=1.0) as client:
            response = await client.get(base_url)
            return response.status_code == 200
    except httpx.RequestError:
        return False


@pytest.fixture(scope="function")
def prompt_setup(tmp_path: Path):
    """
    Creates a temporary valid prompt template for intent classification.
    """
    base_dir = tmp_path / "prompts"
    prompt_dir = base_dir / "cognitive" / "intent_classification"
    prompt_dir.mkdir(parents=True, exist_ok=True)

    # Simplified prompt for small models
    prompt_content = {
        "name": "cognitive/intent_classification",
        "version": "1.0.0",
        "description": "Integration Test Classification Prompt",
        "input_variables": ["query", "history"],
        "template": (
            "Classify user query.\n"
            "Query: {{ query }}\n"
            "History: {{ history }}\n"
            "Intents: SEARCH, ASK, SUMMARIZE, TOOL_USE\n"
            "Output JSON matching IntentClassification schema."
        ),
    }

    with open(prompt_dir / "v1.0.0.yaml", "w", encoding="utf-8") as f:
        yaml.dump(prompt_content, f)

    return str(base_dir)


@pytest.fixture(scope="function", autouse=True)
def setup_cognitive_settings(monkeypatch, prompt_setup):
    monkeypatch.setenv(
        "NALA_SETTINGS_FILES",
        "tests/settings/ai/cognitive/test_int_cognitive_flow.toml",
    )

    get_settings.cache_clear()
    importlib.reload(settings_module)

    settings = get_settings()
    settings.ai.prompts.provider.base_path = prompt_setup

    if hasattr(settings.ai, "connections"):
        llm_manager.settings = settings.ai.connections

    yield

    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="function")
async def cognitive_service() -> AsyncGenerator[CognitiveBaseService, None]:
    if not await check_ollama_health():
        pytest.skip("Skipping Cognitive Integration: Ollama not reachable.")

    # --- Robust Singleton Reset ---
    if llm_manager.is_running() or llm_manager.is_ready():
        await llm_manager.stop()

    if isinstance(llm_manager, BaseService):
        llm_manager._is_closed = False
        if hasattr(llm_manager, "_ready"):
            llm_manager._ready.clear()
        if hasattr(llm_manager, "_run_task"):
            llm_manager._run_task = None

    if hasattr(llm_manager, "_managed_clients"):
        llm_manager._managed_clients.clear()

    # --- Initialization ---
    await llm_manager.start()
    await llm_manager.wait_ready()

    service = CognitiveFactory.create()
    await service.connect()
    await service.wait_ready()

    yield service

    if hasattr(service, "stop"):
        await service.stop()

    await llm_manager.stop()


async def test_cognitive_classification_e2e_search(
    cognitive_service: CognitiveBaseService,
):
    """
    Scenario: User asks a clear search question.
    """
    query = "Find the invoice #12345 from last month."
    print(f"\n[TEST] Classifying query: '{query}'")

    result = await cognitive_service.classify(query=query)

    print(f"[RESULT] Intent: {result.primary_intent}")
    print(f"[RESULT] Confidence: {result.confidence}")
    print(f"[RESULT] Entities: {result.detected_entities}")

    # Plumbing check: Did we get a valid intent object back?
    assert result.primary_intent is not None
    # Loose check for intent (small models might say TOOL_USE or SEARCH)
    assert result.primary_intent in [UserIntent.SEARCH, UserIntent.TOOL_USE]
    # Check that schema validation worked (confidence exists, even if 0.0)
    assert isinstance(result.confidence, float)
    assert result.confidence >= 0.0


async def test_cognitive_classification_e2e_greeting(
    cognitive_service: CognitiveBaseService,
):
    """
    Scenario: User says hello.
    """
    query = "Hello, how are you today?"

    result = await cognitive_service.classify(query=query)

    print(f"[RESULT] Greeting Intent: {result.primary_intent}")

    # Plumbing check: Valid object returned
    assert result.primary_intent is not None
    # Accept broader range of intents for small models
    # They often confuse "Hello" with a "Search" query or "Ask"
    assert result.primary_intent in [
        UserIntent.ASK,
        UserIntent.SEARCH,
        UserIntent.UNKNOWN,
    ]
