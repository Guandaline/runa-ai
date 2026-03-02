import time
import uuid
from typing import Any, Dict, List, Optional

from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.schemas import ChatMessage, MessageRole
from nala.athomic.ai.schemas.llms import LLMResponse
from nala.athomic.ai.schemas.tools import ToolOutput
from nala.athomic.config.schemas.ai import AgentProfileSettings
from nala.athomic.observability import get_logger
from nala.athomic.observability.tracing.instrumentation import AgentTracing
from nala.athomic.services import BaseService
from nala.athomic.services.exceptions import ServiceNotReadyError

from ..tools.protocol import AIToolProtocol
from .executors.base import BaseToolExecutor
from .exreptions import AgentMaxIterationsError
from .persistence.protocol import CheckpointProtocol

logger = get_logger(__name__)


class AgentService(BaseService):
    """
    The core runtime service for an AI Agent.

    This service implements the ReAct (Reasoning + Acting) loop, orchestrating
    interactions between the LLM (Reasoning Engine) and the Tool Executor (Acting Engine).
    It optionally supports state persistence via a CheckpointProtocol, allowing for
    long-running, resilient conversations.
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
        Initializes the AgentService.

        Args:
            settings: Configuration profile defining agent behavior and constraints.
            llm: The Language Model provider instance.
            executor: The strategy for executing tool calls.
            checkpointer: Optional provider for persisting agent state.
            thread_id: Unique identifier for the conversation thread.
        """
        super().__init__(
            service_name=f"agent_service_{settings.name}",
            enabled=True,
        )
        self.settings = settings
        self.llm = llm
        self.executor = executor
        self.checkpointer = checkpointer
        self.thread_id = thread_id

        self.tracing = AgentTracing()

        self._available_tools: List[AIToolProtocol] = []

        # Internal State (Mutable)
        self._history: List[ChatMessage] = []
        self._variables: Dict[str, Any] = {}
        self._current_step: int = 0

    async def _connect(self) -> None:
        """
        Initializes the agent resources.

        Connects the Tool Executor and the Persistence Checkpointer (if it is a
        managed service), ensuring all dependencies are ready before handling requests.
        """
        if not self.executor.is_ready():
            await self.executor.connect()
            await self.executor.wait_ready()

        if isinstance(self.checkpointer, BaseService):
            if not self.checkpointer.is_ready():
                await self.checkpointer.connect()
                await self.checkpointer.wait_ready()

        self._available_tools = self.executor.get_tools_for_agent(self.settings.tools)

        logger.info(
            "Agent '{}' connected. Tools: {}. Persistence: {}.",
            self.settings.name,
            len(self._available_tools),
            "Enabled" if self.checkpointer else "Disabled",
        )

        await self.set_ready()

    async def _close(self) -> None:
        """
        Stops the agent service and associated components.
        """
        if self.executor.is_ready():
            await self.executor.stop()

        logger.info("Agent Service '{}' stopped.", self.settings.name)

    async def run(
        self,
        input_message: str,
        history: Optional[List[ChatMessage]] = None,
        **kwargs: Any,
    ) -> str:
        """
        Executes the agent loop for a given user input.

        Orchestrates the Think-Act-Observe cycle until the agent produces a final
        response or reaches the iteration limit. Handles state hydration and persistence
        automatically if configured.

        Args:
            input_message: The user's query or instruction.
            history: Optional existing conversation history. If persistence is active,
                     stored history takes precedence.
            **kwargs: Additional context or overrides.

        Returns:
            The final text response from the agent.

        Raises:
            ServiceNotReadyError: If the service is not started.
            TimeoutError: If execution exceeds max_execution_time_seconds.
            AgentMaxIterationsError: If the loop limit is reached without conclusion.
        """
        if not self.is_ready():
            raise ServiceNotReadyError(self.service_name)

        start_time = time.monotonic()
        run_id = str(uuid.uuid4())

        self.tracing.on_agent_start(
            run_id=run_id,
            agent_name=self.settings.name,
            metadata={"thread_id": self.thread_id, "model": self.settings.model_name},
        )

        try:
            current_history = await self._initialize_history(history)

            current_history.append(
                ChatMessage(role=MessageRole.USER, content=input_message)
            )
            self._history = current_history

            iteration_count = 0

            while iteration_count < self.settings.max_iterations:
                if (
                    time.monotonic() - start_time
                ) > self.settings.max_execution_time_seconds:
                    raise TimeoutError("Agent execution timeout exceeded.")

                iteration_count += 1
                self._current_step += 1

                response = await self._generate_step(self._history)

                assistant_msg = self._convert_response_to_message(response)
                self._history.append(assistant_msg)

                await self._save_checkpoint(self._history, self._current_step)

                if not response.tool_calls:
                    self.tracing.on_run_end(
                        run_id, outputs={"response": response.content}
                    )
                    return response.content or ""

                logger.debug(
                    "Agent calling tools: {}",
                    [tc.name for tc in response.tool_calls],
                )

                for tool_call in response.tool_calls:
                    self.tracing.on_tool_start(
                        run_id=tool_call.id,
                        tool_name=tool_call.name,
                        tool_input=str(tool_call.arguments),
                        parent_run_id=run_id,
                    )

                tool_outputs = await self.executor.execute_batch(response.tool_calls)

                for output in tool_outputs:
                    self.tracing.on_run_end(
                        run_id=output.tool_call_id, outputs={"result": output.content}
                    )

                    tool_msg = self._convert_output_to_message(output)
                    self._history.append(tool_msg)

                await self._save_checkpoint(self._history, self._current_step)

            raise AgentMaxIterationsError("Agent failed to reach a conclusion.")

        except Exception as e:
            logger.error("Agent execution failed: {}", e)
            self.tracing.on_run_error(run_id, e)
            raise

    async def _generate_step(self, history: List[ChatMessage]) -> LLMResponse:
        """
        Invokes the LLM to generate the next step (thought or action).

        Args:
            history: The full conversation history including system prompt.

        Returns:
            The LLM response containing content and/or tool calls.
        """
        messages_payload = [msg.model_dump(exclude_none=True) for msg in history]

        generate_kwargs = {
            "messages": messages_payload,
            "tools": self._available_tools,
            "temperature": self.settings.temperature,
        }

        if self.settings.model_name:
            generate_kwargs["model"] = self.settings.model_name

        try:
            return await self.llm.generate(**generate_kwargs)
        except Exception as e:
            logger.error("LLM Generation failed: {}", e, exc_info=True)
            raise

    # --- Persistence Helpers ---

    async def _initialize_history(
        self, argument_history: Optional[List[ChatMessage]]
    ) -> List[ChatMessage]:
        """
        Prepares the initial conversation history.

        Logic:
        1. Attempts to load persisted state if checkpointer is configured.
        2. If no persisted state, uses the history provided in arguments.
        3. Ensures the System Prompt is always present at the beginning.

        Args:
            argument_history: History passed via the run() arguments.

        Returns:
            The consolidated list of ChatMessages.
        """
        history: List[ChatMessage] = []

        if self.checkpointer and self.thread_id:
            try:
                state = await self.checkpointer.load(self.thread_id)
                if state and "history" in state:
                    history = [ChatMessage(**msg) for msg in state["history"]]
                    self._current_step = state.get("step", 0)
                    self._variables = state.get("variables", {})
                    logger.debug(
                        "Restored {} messages for thread '{}'.",
                        len(history),
                        self.thread_id,
                    )
            except Exception as e:
                logger.error(
                    "Failed to restore agent state for thread '{}': {}. Starting fresh.",
                    self.thread_id,
                    e,
                )

        if not history and argument_history:
            history = argument_history.copy()

        if not any(msg.role == MessageRole.SYSTEM for msg in history):
            history.insert(
                0,
                ChatMessage(
                    role=MessageRole.SYSTEM, content=self.settings.system_prompt
                ),
            )

        return history

    async def _save_checkpoint(self, history: List[ChatMessage], step: int) -> None:
        """
        Saves the current execution state to the configured checkpointer.

        Args:
            history: Current conversation history.
            step: Current iteration step count.
        """
        if not self.checkpointer or not self.thread_id:
            return

        state_payload = {
            "history": [msg.model_dump() for msg in history],
            "step": step,
            "variables": self._variables,
            "updated_at": str(uuid.uuid4()),
            "agent_profile": self.settings.name,
        }

        try:
            await self.checkpointer.save(self.thread_id, state_payload)
        except Exception as e:
            logger.warning(
                "Failed to save checkpoint for thread '{}': {}", self.thread_id, e
            )

    # --- Converters ---

    def _convert_response_to_message(self, response: LLMResponse) -> ChatMessage:
        """Converts the LLM response object into a standardized ChatMessage."""
        return ChatMessage(
            role=MessageRole.ASSISTANT,
            content=response.content,
            metadata={"tool_calls": response.tool_calls} if response.tool_calls else {},
        )

    def _convert_output_to_message(self, output: ToolOutput) -> ChatMessage:
        """Converts a tool execution output into a standardized ChatMessage."""
        return ChatMessage(
            role=MessageRole.TOOL,
            content=output.content,
            tool_call_id=output.tool_call_id,
            name=output.name,
        )
