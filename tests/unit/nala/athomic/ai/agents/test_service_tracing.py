from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from nala.athomic.ai.agents.service import AgentService
from nala.athomic.ai.schemas import LLMResponse, ToolCall, ToolOutput
from nala.athomic.config.schemas.ai import AgentProfileSettings


@pytest.fixture
def mock_dependencies():
    """
    Fixtures for AgentService dependencies.
    """
    settings = AgentProfileSettings(
        name="test_agent",
        description="Test Agent",
        model_name="gpt-4",
        system_prompt="You are a test bot.",
        tools=["test_tool"],
    )
    llm = AsyncMock()

    executor = AsyncMock()
    executor.is_ready.return_value = True
    executor.get_tools_for_agent = MagicMock(return_value=[])

    return settings, llm, executor


@pytest.mark.asyncio
async def test_agent_run_tracing_flow_success(mock_dependencies):
    """
    Verifies that tracing methods are called correctly during a successful agent run
    involving a tool call.
    """
    settings, llm, executor = mock_dependencies

    # 1. Setup Mock Responses
    # First LLM call returns a tool call
    tool_call = ToolCall(id="call_123", name="test_tool", arguments={"query": "data"})

    response_with_tool = LLMResponse(
        content=None, tool_calls=[tool_call], finish_reason="tool_calls", model="gpt-4"
    )

    # Second LLM call returns final answer
    response_final = LLMResponse(
        content="Final answer", tool_calls=[], finish_reason="stop", model="gpt-4"
    )

    llm.generate.side_effect = [response_with_tool, response_final]

    # Mock Tool Execution
    tool_output = ToolOutput(
        tool_call_id="call_123", name="test_tool", content="Tool Result"
    )
    executor.execute_batch.return_value = [tool_output]

    # 2. Patch AgentTracing
    with patch("nala.athomic.ai.agents.service.AgentTracing") as MockTracing:
        mock_tracer_instance = MockTracing.return_value

        service = AgentService(settings=settings, llm=llm, executor=executor)
        await service.connect()

        # 3. Execute Run
        await service.run(input_message="Do something")

        # 4. Verify Tracing Calls

        # --- Check Agent Start ---
        # Call expected: on_agent_start(run_id=..., agent_name=..., metadata=...)
        mock_tracer_instance.on_agent_start.assert_called_once()
        _, kwargs = mock_tracer_instance.on_agent_start.call_args
        run_id = kwargs["run_id"]
        assert kwargs["agent_name"] == "test_agent"

        # --- Check Tool Start ---
        # Call expected: on_tool_start(run_id=..., tool_name=..., tool_input=..., parent_run_id=...)
        mock_tracer_instance.on_tool_start.assert_called_once()
        _, kwargs_tool = mock_tracer_instance.on_tool_start.call_args
        assert kwargs_tool["tool_name"] == "test_tool"
        assert kwargs_tool["parent_run_id"] == run_id

        # --- Check Run End (Called multiple times) ---
        # on_run_end is called for:
        # 1. Tool execution (run_id="call_123")
        # 2. Agent execution (run_id=run_id)

        call_args_list = mock_tracer_instance.on_run_end.call_args_list

        # Helper to find if a specific run_id was finished
        def was_run_finished(target_id):
            for call in call_args_list:
                # Check positional args (args[0]) OR keyword args (kwargs['run_id'])
                called_id = call.args[0] if call.args else call.kwargs.get("run_id")
                if called_id == target_id:
                    return True
            return False

        # Verify Tool Finished
        assert was_run_finished("call_123"), "on_run_end not called for tool execution"

        # Verify Agent Finished
        assert was_run_finished(run_id), "on_run_end not called for agent execution"


@pytest.mark.asyncio
async def test_agent_run_tracing_error(mock_dependencies):
    """
    Verifies that on_run_error is called when the agent encounters an exception.
    """
    settings, llm, executor = mock_dependencies

    # Setup LLM to raise an exception
    llm.generate.side_effect = Exception("LLM API Failure")

    with patch("nala.athomic.ai.agents.service.AgentTracing") as MockTracing:
        mock_tracer_instance = MockTracing.return_value

        service = AgentService(settings=settings, llm=llm, executor=executor)
        await service.connect()

        # Execute Run and expect failure
        with pytest.raises(Exception, match="LLM API Failure"):
            await service.run(input_message="Crash me")

        # Verify Error Tracing
        mock_tracer_instance.on_agent_start.assert_called_once()
        mock_tracer_instance.on_run_error.assert_called_once()

        # Verify arguments for on_run_error
        args, kwargs = mock_tracer_instance.on_run_error.call_args

        # Check positional args (run_id, error)
        # Expected: on_run_error(run_id, exception)
        exception_arg = args[1] if len(args) > 1 else kwargs.get("error")

        assert isinstance(exception_arg, Exception)
        assert str(exception_arg) == "LLM API Failure"
