import asyncio
from typing import Any, Dict

import pytest

from nala.athomic.ai.workflow.definition.structure import WorkflowDefinition
from nala.athomic.ai.workflow.exceptions import (
    NodeExecutionError,
    WorkflowDefinitionError,
    WorkflowError,
)
from nala.athomic.ai.workflow.providers.memory import InMemoryWorkflowEngine
from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)

# --- Fixtures & Helpers ---


@pytest.fixture
def workflow_settings():
    return WorkflowSettings(
        ENABLED=True,
        DEFAULT_PROVIDER="memory",
        MAX_EXECUTION_STEPS=10,
        DEBUG_MODE=True,
    )


@pytest.fixture
def engine(workflow_settings):
    # Returns an unstarted engine
    return InMemoryWorkflowEngine(settings=workflow_settings)


async def step_increment(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simple node that increments a counter."""
    await asyncio.sleep(0)  # Simulate async work
    return {"count": state.get("count", 0) + 1}


async def step_double(state: Dict[str, Any]) -> Dict[str, Any]:
    """Simple node that doubles the counter."""
    await asyncio.sleep(0)  # Simulate async work
    return {"count": state.get("count", 0) * 2}


async def step_fail(state: Dict[str, Any]) -> Dict[str, Any]:
    """Node that explicitly raises an error."""
    raise ValueError("Intentional failure")


# --- Tests ---


@pytest.mark.asyncio
async def test_linear_execution(engine):
    """
    Verifies a simple linear sequence: Start -> Increment -> Double -> End.
    """
    await engine.start()  # Start the service

    try:
        # 1. Define
        definition = WorkflowDefinition()
        definition.add_step("increment", step_increment)
        definition.add_step("double", step_double)

        definition.set_entry_point("increment")
        definition.add_route("increment", "double")

        # 2. Compile
        engine.compile(definition)

        # 3. Run
        initial_state = {"count": 1}
        final_state = await engine.run(initial_state)

        assert final_state["count"] == 4
    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_conditional_execution(engine):
    """
    Verifies branching logic.
    """
    await engine.start()

    try:
        # 1. Define
        definition = WorkflowDefinition()
        definition.add_step("start", step_increment)  # Adds 1
        definition.add_step("process_high", step_double)
        definition.add_step("process_low", step_increment)

        definition.set_entry_point("start")

        def check_value(state: Dict[str, Any]) -> str:
            return "high" if state["count"] > 5 else "low"

        definition.add_conditional_route(
            source="start",
            condition_fn=check_value,
            destinations={"high": "process_high", "low": "process_low"},
        )

        engine.compile(definition)

        # Case A: Low Path (Input 0 -> Start(1) -> Low(2))
        state_low = await engine.run({"count": 0})
        assert state_low["count"] == 2

        # Case B: High Path (Input 10 -> Start(11) -> High(22))
        state_high = await engine.run({"count": 10})
        assert state_high["count"] == 22
    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_max_execution_steps_limit(workflow_settings):
    """
    Verifies that infinite loops are caught by the MAX_EXECUTION_STEPS limit.
    """
    # Override settings for this test
    workflow_settings.max_execution_steps = 3
    engine = InMemoryWorkflowEngine(settings=workflow_settings)
    await engine.start()

    try:
        # Create an infinite loop: A -> B -> A
        definition = WorkflowDefinition()
        definition.add_step("step_a", step_increment)
        definition.add_step("step_b", step_increment)

        definition.set_entry_point("step_a")
        definition.add_route("step_a", "step_b")
        definition.add_route("step_b", "step_a")

        engine.compile(definition)

        with pytest.raises(WorkflowError) as exc_info:
            await engine.run({"count": 0})

        assert "exceeded maximum execution steps" in str(exc_info.value)
    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_node_execution_failure(engine):
    """
    Verifies that exceptions within nodes are wrapped in NodeExecutionError.
    """
    await engine.start()
    try:
        definition = WorkflowDefinition()
        definition.add_step("step_bad", step_fail)
        definition.set_entry_point("step_bad")

        engine.compile(definition)

        with pytest.raises(NodeExecutionError) as exc_info:
            await engine.run({})

        assert "step_bad" in exc_info.value.node_name
        assert "Intentional failure" in str(exc_info.value)
    finally:
        await engine.stop()


def test_compilation_validation_missing_entry(engine):
    """Verifies validation logic: Missing entry point."""
    definition = WorkflowDefinition()
    definition.add_step("step_a", step_increment)

    with pytest.raises(WorkflowDefinitionError) as exc:
        engine.compile(definition)
    assert "no entry point" in str(exc.value)


def test_compilation_validation_invalid_route(engine):
    """Verifies validation logic: Route to non-existent node."""
    definition = WorkflowDefinition()
    definition.add_step("step_a", step_increment)
    definition.set_entry_point("step_a")
    definition.add_route("step_a", "ghost_node")

    with pytest.raises(WorkflowDefinitionError) as exc:
        engine.compile(definition)
    assert "Route destination 'ghost_node' not found" in str(exc.value)


@pytest.mark.asyncio
async def test_service_lifecycle(engine):
    """
    Verifies that the engine respects the BaseService lifecycle.
    """
    # 1. Before execution
    assert not engine.is_connected()

    await engine.start()
    assert engine.is_ready()
    assert engine.is_connected()

    # 2. Run
    definition = WorkflowDefinition()
    definition.add_step("a", step_increment)
    definition.set_entry_point("a")
    engine.compile(definition)

    await engine.run({"count": 0})

    # 3. Stop
    await engine.stop()
    assert engine.is_closed()
    assert not engine.is_connected()

    # 4. Run after stop should fail
    # Since we fixed the exception to ServiceUnavailableError
    from nala.athomic.services.exceptions import ServiceUnavailableError

    with pytest.raises(ServiceUnavailableError):
        await engine.run({"count": 0})
