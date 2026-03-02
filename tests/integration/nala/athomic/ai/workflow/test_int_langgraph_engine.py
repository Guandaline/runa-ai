import asyncio
import importlib
from typing import Any, AsyncGenerator, Dict

import pytest
import pytest_asyncio

from nala.athomic.ai.workflow.definition.structure import WorkflowDefinition
from nala.athomic.ai.workflow.exceptions import WorkflowError
from nala.athomic.ai.workflow.factory import WorkflowEngineFactory
from nala.athomic.ai.workflow.protocol import WorkflowEngineProtocol
from nala.athomic.config import get_settings
from nala.athomic.config import settings as settings_module

# Skip if library doesn't exist
langgraph = pytest.importorskip("langgraph")

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio(loop_scope="module"),
    pytest.mark.ai,
]

# --- Configuration Fixtures (Nala Standard) ---


@pytest.fixture(scope="function", autouse=True)
def setup_workflow_settings(monkeypatch):
    """
    Loads the specific TOML file for Workflow tests.
    Follows the module reload pattern found in 'test_int_cognitive_flow.py' and others.
    """
    monkeypatch.setenv(
        "NALA_SETTINGS_FILES",
        "tests/settings/ai/workflow/test_int_langgraph_workflow.toml",
    )

    get_settings.cache_clear()
    importlib.reload(settings_module)

    yield

    get_settings.cache_clear()


@pytest_asyncio.fixture(scope="function")
async def engine_service() -> AsyncGenerator[WorkflowEngineProtocol, None]:
    """
    Initializes the Engine using the Factory and manages the lifecycle (Start/Stop).
    Pattern identified in 'test_int_agent_flow.py'.
    """
    settings = get_settings().ai.workflow

    # Sanity check
    assert (
        settings.default_provider == "langgraph"
    ), "Configuration didn't properly load langgraph provider"

    service = WorkflowEngineFactory.create(settings)

    # Standard BaseService lifecycle hook
    if hasattr(service, "connect"):
        await service.connect()

    if hasattr(service, "start"):
        await service.start()

    if hasattr(service, "wait_ready"):
        await service.wait_ready()

    yield service

    if hasattr(service, "stop"):
        await service.stop()


# --- Helper Functions (Graph Nodes) ---


async def node_start(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0)  # Simulate async operation
    return {"value": state.get("value", 0), "path": ["start"]}


async def node_add(state: Dict[str, Any]) -> Dict[str, Any]:
    current_value = state.get("value", 0)
    current_path = state.get("path", [])
    await asyncio.sleep(0)  # Simulate async operation
    return {"value": current_value + 1, "path": current_path + ["add"]}


async def node_multiply(state: Dict[str, Any]) -> Dict[str, Any]:
    current_value = state.get("value", 0)
    current_path = state.get("path", [])
    await asyncio.sleep(0)  # Simulate async operation
    return {"value": current_value * 2, "path": current_path + ["multiply"]}


# --- Integration Tests ---


async def test_langgraph_linear_execution(engine_service: WorkflowEngineProtocol):
    """
    Validates execution of a simple linear graph: Start -> Add -> Multiply.
    Verifies that state flows correctly between nodes.
    """
    # 1. Definition
    definition = WorkflowDefinition()
    definition.add_step("start", node_start)
    definition.add_step("add", node_add)
    definition.add_step("multiply", node_multiply)

    definition.set_entry_point("start")
    definition.add_route("start", "add")
    definition.add_route("add", "multiply")

    # 2. Compilation
    engine_service.compile(definition)

    # 3. Execution
    initial_state = {"value": 5}
    print(f"\n[TEST] Executing Linear Workflow with initial: {initial_state}")

    result = await engine_service.run(initial_state)

    print(f"[RESULT] Final State: {result}")

    # 4. Assertions
    # Logic: 5 (Start) -> 5+1=6 (Add) -> 6*2=12 (Multiply)
    assert result["value"] == 12
    assert result["path"] == ["start", "add", "multiply"]


async def test_langgraph_conditional_routing(engine_service: WorkflowEngineProtocol):
    """
    Validates conditional routing.
    If value > 10 -> Multiply. Otherwise -> Add.
    """
    definition = WorkflowDefinition()
    definition.add_step("start", node_start)
    definition.add_step("process_high", node_multiply)
    definition.add_step("process_low", node_add)

    definition.set_entry_point("start")

    def router_logic(state: Dict[str, Any]) -> str:
        return "high" if state["value"] > 10 else "low"

    definition.add_conditional_route(
        source="start",
        condition_fn=router_logic,
        destinations={"high": "process_high", "low": "process_low"},
    )

    engine_service.compile(definition)

    # Case 1: Low Value (5) -> Should go to Add -> Result 6
    res_low = await engine_service.run({"value": 5})
    assert res_low["value"] == 6  # 5 (start) -> router low -> 5+1 (add)
    assert "add" in res_low["path"]

    # Case 2: High Value (20) -> Should go to Multiply -> Result 40
    res_high = await engine_service.run({"value": 20})
    assert res_high["value"] == 40  # 20 (start) -> router high -> 20*2 (multiply)
    assert "multiply" in res_high["path"]


async def test_langgraph_recursion_limit_enforcement(
    engine_service: WorkflowEngineProtocol,
):
    """
    Verifies that the recursion limit defined in settings.toml (max_execution_steps=10)
    is respected by LangGraph, preventing infinite loops.
    """
    definition = WorkflowDefinition()
    definition.add_step("ping", node_add)
    definition.add_step("pong", node_add)

    definition.set_entry_point("ping")
    # Infinite Loop: Ping -> Pong -> Ping ...
    definition.add_route("ping", "pong")
    definition.add_route("pong", "ping")

    engine_service.compile(definition)

    print("\n[TEST] Executing Infinite Loop Workflow (expecting error)...")

    # We expect the engine to raise WorkflowError (wrapper for GraphRecursionError)
    with pytest.raises(WorkflowError) as exc_info:
        await engine_service.run({"value": 0})

    print(f"[RESULT] Caught expected error: {exc_info.value}")
    assert "Max execution steps" in str(exc_info.value)
    assert "exceeded" in str(exc_info.value)
