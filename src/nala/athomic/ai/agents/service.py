import time
from typing import Any, Dict, List, Optional

from nala.athomic.context.context_vars import get_request_id
from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.schemas import ChatMessage, MessageRole, ToolCall
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.ai.schemas.tools import ToolOutput
from nala.athomic.config.schemas.ai import AgentProfileSettings
from nala.athomic.observability import get_logger
from nala.athomic.observability.tracing.instrumentation import AgentTracing
from nala.athomic.services import BaseService

from ..tools.protocol import AIToolProtocol
from .executors.base import BaseToolExecutor
from .exreptions import AgentMaxIterationsError
from .parsers import AgentResponseParser
from .persistence.protocol import CheckpointProtocol

logger = get_logger(__name__)


class AgentService(BaseService):
    """
    Stateless Agent Orchestrator.

    This service implements the ReAct loop without storing conversation state
    in instance variables. All state is managed locally within the run method
    to ensure thread safety and allow singleton usage.
    """

    def __init__(
        self,
        settings: AgentProfileSettings,
        llm: BaseLLM,
        executor: BaseToolExecutor,
        checkpointer: Optional[CheckpointProtocol] = None,
        thread_id: Optional[str] = None,
    ):
        """
        Initializes the agent engine. Instance variables are for shared resources only.
        """
        super().__init__(
            service_name=f"agent_service_{settings.name}",
            enabled=True,
        )
        self.settings = settings
        self.llm = llm
        self.executor = executor
        self.checkpointer = checkpointer
        # Instance thread_id acts as a default if not provided in run()
        self.thread_id = thread_id

        self.tracing = AgentTracing()
        self.parser = AgentResponseParser()
        self._available_tools: List[AIToolProtocol] = []

    async def _connect(self) -> None:
        """Initializes shared tool resources."""
        if not self.executor.is_ready():
            await self.executor.connect()
            await self.executor.wait_ready()

        self._available_tools = self.executor.get_tools_for_agent(self.settings.tools)
        await self.set_ready()

    async def run(
        self,
        input_message: str,
        thread_id: Optional[str] = None,
        history: Optional[List[ChatMessage]] = None,
        **context: Any,
    ) -> str:
        """
        Executes the reasoning loop with dynamic runtime context.

        Args:
            input_message: The user's query.
            thread_id: Dynamic session identifier for persistence.
            history: Optional seed history.
            **context: Dynamic variables (e.g., employee_id) to be injected into tools.
        """
        if not self.is_ready():
            await self.start()
            await self.wait_ready()

        # Resolve identity from context (Infrastructure) or parameters
        execution_id = get_request_id() or f"exec_{int(time.time())}"
        active_thread_id = thread_id or self.thread_id

        start_time = time.monotonic()
        self.tracing.on_agent_start(execution_id, self.settings.name)

        # Thread-local history and state
        local_history = await self._initialize_state(active_thread_id, history)
        local_history.append(ChatMessage(role=MessageRole.USER, content=input_message))

        iteration_count = 0

        try:
            while iteration_count < self.settings.max_iterations:
                if (
                    time.monotonic() - start_time
                ) > self.settings.max_execution_time_seconds:
                    raise TimeoutError("Agent execution timeout.")

                iteration_count += 1

                # 1. Reasoning
                response = await self._generate_step(local_history)
                clean_content, tool_calls = self.parser.parse(response)

                # 2. Context Injection (Safety middleware for arguments)
                if tool_calls and context:
                    self._inject_context_to_tools(tool_calls, context)

                assistant_msg = self._convert_response_to_message(
                    clean_content, tool_calls
                )
                local_history.append(assistant_msg)

                if not tool_calls:
                    await self._save_checkpoint(
                        active_thread_id, local_history, iteration_count, context
                    )
                    return clean_content or ""

                # 3. Acting
                tool_outputs = await self.executor.execute_batch(tool_calls)
                for output in tool_outputs:
                    local_history.append(self._convert_output_to_message(output))

                await self._save_checkpoint(
                    active_thread_id, local_history, iteration_count, context
                )

            raise AgentMaxIterationsError("Agent failed to reach a conclusion.")
        except Exception as e:
            logger.error("Execution failed for trace {}: {}", execution_id, e)
            raise

    def _inject_context_to_tools(
        self, tool_calls: List[ToolCall], context: Dict[str, Any]
    ) -> None:
        """
        Maps dynamic context variables to tool arguments if missing.
        """
        for tool_call in tool_calls:
            for key, value in context.items():
                if key not in tool_call.arguments:
                    tool_call.arguments[key] = value
                    logger.debug(
                        "Injected context '{}' into tool '{}'.", key, tool_call.name
                    )

    async def _generate_step(self, history: List[ChatMessage]) -> LLMResponse:
        """Invokes LLM provider with local history."""
        payload = [msg.model_dump(exclude_none=True) for msg in history]
        return await self.llm.generate(
            messages=payload, tools=self._available_tools, temperature=0.0
        )

    async def _initialize_state(
        self, thread_id: Optional[str], arg_history: Optional[List[ChatMessage]]
    ) -> List[ChatMessage]:
        """Loads conversation history from checkpointer."""
        history = []
        if self.checkpointer and thread_id:
            state = await self.checkpointer.load(thread_id)
            if state:
                history = [ChatMessage(**msg) for msg in state.get("history", [])]

        if not history and arg_history:
            history = arg_history.copy()

        if not any(msg.role == MessageRole.SYSTEM for msg in history):
            history.insert(
                0,
                ChatMessage(
                    role=MessageRole.SYSTEM, content=self.settings.system_prompt
                ),
            )

        return history

    async def _save_checkpoint(
        self,
        thread_id: Optional[str],
        history: List[ChatMessage],
        step: int,
        context: Dict[str, Any],
    ) -> None:
        """Persists session state."""
        if self.checkpointer and thread_id:
            await self.checkpointer.save(
                thread_id,
                {
                    "history": [msg.model_dump() for msg in history],
                    "step": step,
                    "variables": context,
                    "agent": self.settings.name,
                },
            )

    def _convert_response_to_message(
        self, content: Optional[str], tool_calls: List[ToolCall]
    ) -> ChatMessage:
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=content,
            metadata={"tool_calls": tool_calls} if tool_calls else None,
        )

    def _convert_output_to_message(self, output: ToolOutput) -> ChatMessage:
        return ChatMessage(
            role=MessageRole.TOOL,
            content=output.content,
            tool_call_id=output.tool_call_id,
            name=output.name,
        )
