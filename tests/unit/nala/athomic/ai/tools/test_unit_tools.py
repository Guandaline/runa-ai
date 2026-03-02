# tests/unit/nala/athomic/ai/tools/test_unit_tools.py
import asyncio
from enum import Enum
from typing import Optional

import pytest

from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.ai.tools.decorator import ai_tool
from nala.athomic.ai.tools.exceptions import ToolExecutionError, ToolNotFoundError
from nala.athomic.ai.tools.registry import tool_registry
from nala.athomic.ai.tools.schema import SchemaGenerator

# --- Fixtures & Helpers ---


class WeatherUnit(str, Enum):
    CELSIUS = "celsius"
    FAHRENHEIT = "fahrenheit"


def sample_sync_function(location: str, unit: WeatherUnit = WeatherUnit.CELSIUS) -> str:
    """Get weather for a location."""
    # .value is safe to access because FunctionTool ensures 'unit' is an Enum instance
    return f"Weather in {location} is 25 {unit.value}"


async def sample_async_function(location: str) -> str:
    """Async weather fetcher."""
    await asyncio.sleep(0.01)
    return f"Async weather in {location}"


def failing_function(arg: int) -> int:
    """This function always fails."""
    raise ValueError("Something went wrong")


@pytest.fixture(autouse=True)
async def clear_registry():
    """Ensure a clean registry state before each test."""
    await tool_registry.clear()


# --- Schema Generator Tests ---


def test_schema_generator_basic():
    """Tests if schema generation works for simple types and enums."""
    schema = SchemaGenerator.generate(sample_sync_function)

    assert schema["type"] == "object"
    props = schema["properties"]

    # Check 'location' field
    assert "location" in props
    assert props["location"]["type"] == "string"

    # Check 'unit' enum field handling in Pydantic V2
    assert "unit" in props
    # It might be a direct definition or a $ref depending on Pydantic internals
    # But checking required fields is stable
    assert "location" in schema["required"]
    assert "unit" not in schema["required"]  # It has a default

    # Verify Enum values are present somewhere (either inline or in $defs)
    import json

    schema_str = json.dumps(schema)
    assert "celsius" in schema_str
    assert "fahrenheit" in schema_str


def test_schema_generator_complex_types():
    """Tests handling of Optional and complex types."""

    def complex_func(
        user_id: int, meta: Optional[str] = None, flags: bool = True
    ) -> None: ...

    schema = SchemaGenerator.generate(complex_func)
    props = schema["properties"]

    assert props["user_id"]["type"] == "integer"
    assert "meta" in props
    assert "type" in props["meta"] or "anyOf" in props["meta"]
    assert props["flags"]["type"] == "boolean"
    assert "user_id" in schema["required"]
    assert "meta" not in schema["required"]


# --- Decorator & Execution Tests ---


@pytest.mark.asyncio
async def test_decorator_sync_execution():
    """Verifies that a sync function decorated with @ai_tool runs correctly in async context."""

    tool = ai_tool(sample_sync_function)

    # Ensure it's ready (FunctionTool effectively is, but good practice)
    await tool.start()

    assert tool.name == "sample_sync_function"
    assert "Get weather" in tool.description

    # Execute passing STRINGS. The tool should coerce 'celsius' -> WeatherUnit.CELSIUS
    result = await tool.execute(location="Florianópolis", unit="celsius")
    assert result == "Weather in Florianópolis is 25 celsius"


@pytest.mark.asyncio
async def test_decorator_async_execution():
    """Verifies that an async function decorated with @ai_tool runs correctly."""

    tool = ai_tool(sample_async_function, name="custom_async_tool")
    await tool.start()

    assert tool.name == "custom_async_tool"

    # Execute
    result = await tool.execute(location="Tokyo")
    assert result == "Async weather in Tokyo"


@pytest.mark.asyncio
async def test_tool_error_handling():
    """Ensures exceptions inside tools are wrapped in ToolExecutionError."""
    tool = ai_tool(failing_function)
    await tool.start()

    with pytest.raises(ToolExecutionError) as exc_info:
        await tool.execute(arg=1)

    assert "Error executing tool 'failing_function'" in str(exc_info.value)
    assert isinstance(exc_info.value.original_error, ValueError)


# --- Registry Tests ---


@pytest.mark.asyncio
async def test_registry_registration_and_retrieval():
    """Tests manual registration and retrieval from registry."""

    @ai_tool(auto_register=True)
    def my_registered_tool(x: int): ...

    # Retrieval
    tool = tool_registry.get("my_registered_tool")
    assert tool is not None
    assert isinstance(tool, BaseTool)

    # Retrieval failure using get_tool (which raises)
    with pytest.raises(ToolNotFoundError):
        tool_registry.get_tool("non_existent_tool")

    # Standard get returns None
    with pytest.raises(ValueError):
        tool_registry.get("non_existent_tool")


@pytest.mark.asyncio
async def test_registry_get_definitions():
    """Tests the generation of the tools list for LLM providers."""

    @ai_tool(name="tool_a", description="Tool A description")
    def func_a(a: int): ...

    @ai_tool(name="tool_b", description="Tool B description")
    def func_b(b: str): ...

    definitions = tool_registry.get_definitions()

    assert len(definitions) == 2

    # Verify structure matches OpenAI/Vertex expectation
    tool_a_def = next(d for d in definitions if d["name"] == "tool_a")
    assert tool_a_def["description"] == "Tool A description"
    assert "parameters" in tool_a_def
    assert tool_a_def["parameters"]["type"] == "object"


@pytest.mark.asyncio
async def test_registry_lifecycle_inheritance():
    """Verifies that the registry inherited BaseInstanceRegistry methods correctly."""

    @ai_tool
    def lifecycle_tool(): ...

    # Check if 'all()' returns the dict
    assert len(tool_registry.all()) == 1

    # Check if clear works (inherited from BaseInstanceRegistry)
    await tool_registry.clear()
    assert len(tool_registry.all()) == 0
