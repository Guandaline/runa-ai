import asyncio
from typing import Any, Dict

import pytest

from nala.athomic.ai.workflow.definition.structure import WorkflowDefinition
from nala.athomic.ai.workflow.exceptions import (
    WorkflowError,
)
from nala.athomic.ai.workflow.providers.langgraph import LangGraphWorkflowEngine
from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)
from nala.athomic.services.exceptions import ServiceUnavailableError

# Skip tests if library missing (Standard pytest practice for integration tests)
langgraph = pytest.importorskip("langgraph")

# --- Fixtures ---


@pytest.fixture
def workflow_settings():
    return WorkflowSettings(
        ENABLED=True,
        DEFAULT_PROVIDER="langgraph",
        MAX_EXECUTION_STEPS=5,
        DEBUG_MODE=True,
    )


@pytest.fixture
def engine(workflow_settings):
    return LangGraphWorkflowEngine(settings=workflow_settings)


# --- Helper Steps ---


async def step_add_one(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0)  # Simulate async operation
    return {"count": state.get("count", 0) + 1}


async def step_multiply_two(state: Dict[str, Any]) -> Dict[str, Any]:
    await asyncio.sleep(0)  # Simulate async operation
    return {"count": state.get("count", 0) * 2}


# --- Tests ---


@pytest.mark.asyncio
async def test_linear_execution_flow(engine):
    """
    Verifies translation of a linear Nala workflow to LangGraph.
    Start -> Add One -> Multiply Two -> End
    Input: 1 -> 2 -> 4
    """
    await engine.start()

    try:
        # 1. Define Nala Workflow
        definition = WorkflowDefinition()
        definition.add_step("add", step_add_one)
        definition.add_step("mult", step_multiply_two)

        definition.set_entry_point("add")
        definition.add_route("add", "mult")

        # 2. Compile
        engine.compile(definition)

        # 3. Run
        result = await engine.run({"count": 1})
        assert result["count"] == 4

    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_conditional_execution_flow(engine):
    """
    Verifies translation of conditional routes (ConditionalEdges).
    """
    await engine.start()

    try:
        definition = WorkflowDefinition()
        definition.add_step("start", step_add_one)  # 1 -> 2
        definition.add_step("big_path", step_multiply_two)  # 2 -> 4
        definition.add_step("small_path", step_add_one)  # 2 -> 3

        definition.set_entry_point("start")

        def router(state):
            return "big" if state["count"] > 5 else "small"

        definition.add_conditional_route(
            source="start",
            condition_fn=router,
            destinations={"big": "big_path", "small": "small_path"},
        )

        engine.compile(definition)

        # Scenario 1: Input 0 -> Start(1) -> Small Path -> 2
        res_small = await engine.run({"count": 0})
        assert res_small["count"] == 2

        # Scenario 2: Input 10 -> Start(11) -> Big Path -> 22
        res_big = await engine.run({"count": 10})
        assert res_big["count"] == 22

    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_recursion_limit_mapping(engine):
    """
    Verifies that Nala's MAX_EXECUTION_STEPS maps to LangGraph's recursion_limit
    and the specific GraphRecursionError is caught and re-raised as WorkflowError.
    """
    await engine.start()

    try:
        # Define infinite loop: A <-> B
        definition = WorkflowDefinition()
        definition.add_step("A", step_add_one)
        definition.add_step("B", step_add_one)

        definition.set_entry_point("A")
        definition.add_route("A", "B")
        definition.add_route("B", "A")

        engine.compile(definition)

        # Run should fail after 5 steps (defined in fixture)
        with pytest.raises(WorkflowError) as exc:
            await engine.run({"count": 0})

        # The engine logic should catch "recursion limit" in the message
        assert "Max execution steps" in str(exc.value)

    finally:
        await engine.stop()


@pytest.mark.asyncio
async def test_service_lifecycle_enforcement(engine):
    """
    Verifies that LangGraph engine also respects the BaseService readiness check.
    """
    definition = WorkflowDefinition()
    definition.add_step("A", step_add_one)
    definition.set_entry_point("A")
    engine.compile(definition)

    # Run WITHOUT start() -> Should fail
    with pytest.raises(ServiceUnavailableError):
        await engine.run({"count": 0})

    # Run WITH start() -> Should pass
    await engine.start()
    res = await engine.run({"count": 0})
    assert res["count"] == 1

    await engine.stop()


def test_compilation_missing_entry_point(engine):
    """
    Verifies that _compile_impl validates the entry point correctly.
    """
    definition = WorkflowDefinition()
    definition.add_step("A", step_add_one)
    # No entry point set

    with pytest.raises(WorkflowError) as exc:
        engine.compile(definition)

    assert "no entry point defined" in str(exc.value)
