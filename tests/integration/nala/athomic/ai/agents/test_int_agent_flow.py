# tests/integration/nala/athomic/ai/agents/test_int_agent_flow.py
import importlib

import pytest

from nala.athomic.ai.agents.factory import AgentFactory
from nala.athomic.ai.agents.service import AgentService
from nala.athomic.ai.llm.manager import llm_manager
from nala.athomic.ai.tools.function_tool import FunctionTool
from nala.athomic.ai.tools.registry import tool_registry
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.ai,
]


class ZeroDivisionErrorForTest(Exception):
    """Custom exception to verify error handling propagation."""

    pass


def calculator_implementation(a: int, b: int, operation: str) -> str:
    """
    Performs basic arithmetic operations to validate tool execution.
    """
    if operation == "add":
        return str(a + b)
    elif operation == "multiply":
        return str(a * b)
    elif operation == "divide":
        if b == 0:
            raise ZeroDivisionErrorForTest("Cannot divide by zero.")
        return str(a / b)
    return "unknown operation"


# --- 2. Infrastructure Setup ---


@pytest.fixture(scope="function", autouse=True)
def setup_agent_environment(monkeypatch):
    """
    Configures the environment for Agent integration testing.
    """
    monkeypatch.setenv(
        "NALA_SETTINGS_FILES", "tests/settings/ai/agents/test_int_agent_flow.toml"
    )

    get_settings.cache_clear()
    importlib.reload(settings_module)

    new_settings = get_settings()
    llm_manager.settings = new_settings.ai.connections

    tool_registry.clear()

    if hasattr(tool_registry, "_registry"):
        tool_registry._registry.clear()

    tool_instance = FunctionTool(
        name="calculator_tool",
        description="Useful for performing mathematical calculations. Supports 'add', 'multiply', and 'divide'.",
        func=calculator_implementation,
    )
    tool_registry.register("calculator_tool", tool_instance)

    yield

    # Cleanup the factory singleton after test
    tool_registry.clear()
    get_settings.cache_clear()


@pytest.fixture
async def agent_service():
    """
    Manages the lifecycle of the AgentService and its dependencies.
    """
    if llm_manager.is_running() or llm_manager._is_closed:
        llm_manager._ready.clear()
        llm_manager._run_task = None
        llm_manager._is_closed = False
        if hasattr(llm_manager, "_managed_clients"):
            llm_manager._managed_clients.clear()
        if hasattr(llm_manager, "managed_services"):
            llm_manager.managed_services.clear()

    await llm_manager.connect()
    await llm_manager.wait_ready()

    service = AgentFactory.create("math_agent")
    await service.connect()
    await service.wait_ready()

    yield service

    await service.stop()
    await llm_manager.stop()


# --- 3. Integration Scenarios ---


async def test_agent_execution_happy_path(agent_service: AgentService):
    """
    Validates the complete 'Think-Act-Observe' loop for a successful request.
    """
    user_prompt = "Calculate 15 multiplied by 4. Give me just the number."

    response = await agent_service.run(user_prompt)

    print(f"\n[TEST] Agent Success Response: {response}")

    assert response is not None
    assert "60" in response


async def test_agent_error_resilience(agent_service: AgentService):
    """
    Validates the Agent's ability to recover from Tool execution errors.
    """
    user_prompt = "Calculate 10 divided by 0."

    response = await agent_service.run(user_prompt)

    print(f"\n[TEST] Resilience Response: {response}")

    assert response is not None

    error_indicators = ["zero", "error", "cannot", "impossible", "undefined"]
    assert any(
        indicator in response.lower() for indicator in error_indicators
    ), f"Agent failed to report error. Response: {response}"
