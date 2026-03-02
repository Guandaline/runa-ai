import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from nala.athomic.ai.agents.executors.base import BaseToolExecutor
from nala.athomic.ai.agents.service import AgentMaxIterationsError, AgentService
from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.schemas import (
    MessageRole,
    ToolCall,
    ToolOutput,
)
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.ai.tools.base import BaseTool
from nala.athomic.ai.tools.registry import ToolRegistry
from nala.athomic.config.schemas.ai import AgentProfileSettings

# --- Fixtures ---


@pytest.fixture
def mock_settings():
    return AgentProfileSettings(
        name="test_agent",
        model_name="gpt-4-mock",
        system_prompt="You are a test bot.",
        tools=["weather_tool", "calc_tool"],
        max_iterations=3,
        max_execution_time_seconds=2,
    )


@pytest.fixture
def mock_llm():
    """Mocks the BaseLLM provider."""
    llm = MagicMock(spec=BaseLLM)
    llm.generate = AsyncMock()
    return llm


@pytest.fixture
def mock_tool_registry():
    registry = MagicMock(spec=ToolRegistry)

    # Setup a valid tool mock
    weather_tool = MagicMock(spec=BaseTool)
    weather_tool.name = "weather_tool"
    weather_tool.schema = {
        "name": "weather_tool",
        "description": "Get weather",
        "parameters": {"type": "object"},
    }

    # Configure get_tool behavior
    def get_tool_side_effect(name):
        if name == "weather_tool":
            return weather_tool
        return None

    registry.get_tool.side_effect = get_tool_side_effect
    return registry


@pytest.fixture
def mock_executor(mock_tool_registry):
    """
    Mocks the BaseToolExecutor.
    Must be an instance of BaseToolExecutor to pass instance checks in _connect.
    """
    executor = MagicMock(spec=BaseToolExecutor)
    executor.tool_registry = mock_tool_registry
    executor.connect = AsyncMock()
    executor.wait_ready = AsyncMock()
    executor.is_ready.return_value = False
    executor.execute_batch = AsyncMock()

    # Default behavior for get_tools_for_agent if not overridden in tests
    executor.get_tools_for_agent.return_value = []

    return executor


@pytest.fixture
async def agent_service(mock_settings, mock_llm, mock_executor):
    service = AgentService(settings=mock_settings, llm=mock_llm, executor=mock_executor)
    # Perform the connect phase to populate tools
    await service.connect()
    await service.wait_ready()
    return service


# --- Tests ---


@pytest.mark.asyncio
async def test_connect_validates_tools(mock_settings, mock_llm, mock_executor):
    """
    Verifies that _connect retrieves the correct tools via the executor.
    """
    mock_tool = MagicMock()
    mock_tool.name = "weather_tool"
    mock_executor.get_tools_for_agent.return_value = [mock_tool]

    service = AgentService(settings=mock_settings, llm=mock_llm, executor=mock_executor)

    await service.connect()

    # The service stores tool instances, not just schemas.
    assert len(service._available_tools) == 1
    assert service._available_tools[0].name == "weather_tool"

    # Verify that the service requested the tools from settings
    mock_executor.get_tools_for_agent.assert_called_with(mock_settings.tools)


@pytest.mark.asyncio
async def test_run_simple_conversation(agent_service, mock_llm):
    """
    Verifies a simple single-turn conversation where the LLM does not call any tools.
    """
    # Setup LLM response
    mock_llm.generate.return_value = LLMResponse(
        content="Hello user!", finish_reason="stop", model="gpt-4-mock"
    )

    response = await agent_service.run("Hi there")

    assert response == "Hello user!"

    # Verify LLM was called with System Prompt and User Message
    call_args = mock_llm.generate.call_args
    assert call_args is not None
    messages = call_args.kwargs["messages"]

    assert len(messages) == 2
    assert messages[0]["role"] == MessageRole.SYSTEM
    assert messages[1]["role"] == MessageRole.USER
    assert messages[1]["content"] == "Hi there"


@pytest.mark.asyncio
async def test_run_with_tool_execution(agent_service, mock_llm, mock_executor):
    """
    Verifies the ReAct loop:
    1. LLM requests tool -> 2. Executor runs tool -> 3. LLM sees output -> 4. Final Answer.
    """
    # Step 1: LLM decides to call a tool
    tool_call = ToolCall(id="call_1", name="weather_tool", arguments={"city": "SP"})
    response_step_1 = LLMResponse(
        content=None,
        tool_calls=[tool_call],
        finish_reason="tool_calls",
        model="gpt-4-mock",
    )

    # Step 2: Executor returns result
    tool_output = ToolOutput(
        tool_call_id="call_1", name="weather_tool", content="Sunny 25C"
    )
    mock_executor.execute_batch.return_value = [tool_output]

    # Step 3: LLM generates final answer based on tool output
    response_step_2 = LLMResponse(
        content="It is sunny in SP.", finish_reason="stop", model="gpt-4-mock"
    )

    # Configure LLM to return sequence of responses
    mock_llm.generate.side_effect = [response_step_1, response_step_2]

    final_response = await agent_service.run("Weather in SP?")

    assert final_response == "It is sunny in SP."

    # Verify Logic Flow
    assert mock_llm.generate.call_count == 2
    mock_executor.execute_batch.assert_awaited_once_with([tool_call])

    # Check history passed to second LLM call
    second_call_messages = mock_llm.generate.call_args_list[1].kwargs["messages"]
    # Expect: System -> User -> Assistant(ToolCall) -> Tool(Result)
    assert len(second_call_messages) == 4
    assert second_call_messages[2]["role"] == MessageRole.ASSISTANT
    assert second_call_messages[3]["role"] == MessageRole.TOOL
    assert second_call_messages[3]["content"] == "Sunny 25C"


@pytest.mark.asyncio
async def test_max_iterations_error(agent_service, mock_llm, mock_executor):
    """
    Verifies that the agent raises AgentMaxIterationsError if it gets stuck in a loop.
    """
    # Force a loop: LLM always asks for a tool
    tool_call = ToolCall(id="loop", name="weather_tool", arguments={})
    loop_response = LLMResponse(
        content=None,
        tool_calls=[tool_call],
        finish_reason="tool_calls",
        model="gpt-4-mock",
    )

    mock_llm.generate.return_value = loop_response
    mock_executor.execute_batch.return_value = [
        ToolOutput(tool_call_id="loop", name="weather_tool", content="looping")
    ]

    # The fixture sets max_iterations=3
    with pytest.raises(AgentMaxIterationsError):
        await agent_service.run("stuck loop")

    # Should have called generate 3 times (max_iterations)
    assert mock_llm.generate.call_count == 3


@pytest.mark.asyncio
async def test_execution_timeout(agent_service, mock_llm, mock_executor):
    """
    Verifies that the agent respects the max_execution_time_seconds setting.
    """
    agent_service.settings.max_execution_time_seconds = 0.1

    # Simulate a slow LLM that returns a ToolCall (forcing the loop to continue)
    async def slow_generate(*args, **kwargs):
        await asyncio.sleep(0.3)  # Sleep longer than the limit (0.1)
        # Return a tool call to force the loop to try to run again
        return LLMResponse(
            content=None,
            tool_calls=[ToolCall(id="t1", name="weather_tool", arguments={})],
            finish_reason="tool_calls",
            model="test",
        )

    mock_llm.generate.side_effect = slow_generate
    mock_executor.execute_batch.return_value = []

    with pytest.raises(TimeoutError):
        await agent_service.run("timeout test")
