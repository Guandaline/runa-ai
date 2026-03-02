# src/nala/athomic/ai/tools/base.py
from abc import abstractmethod
from typing import Any, Dict

from nala.athomic.ai.tools.exceptions import ToolExecutionError
from nala.athomic.ai.tools.protocol import AIToolProtocol
from nala.athomic.observability.tracing import SpanKind, StatusCode
from nala.athomic.services.base import BaseService


class BaseTool(BaseService, AIToolProtocol):
    """
    Abstract base class for AI Tools, integrating the Athomic Service Lifecycle.

    By inheriting from BaseService, every tool gets:
    - Lifecycle management (connect/close/health).
    - Standardized logging and tracing.
    - Prometheus metrics for connection/readiness.

    Subclasses must implement:
    - _execute_tool: The actual business logic.
    - schema (property): The argument definition.
    - _connect (optional): Setup logic (e.g., API login).
    """

    def __init__(
        self,
        name: str,
        description: str,
        enabled: bool = True,
    ):
        """
        Initialize the tool service.

        Args:
            name: Unique identifier for the tool.
            description: Description for the LLM.
            enabled: Master switch for this tool.
        """
        # BaseService initializes the logger and tracer using the service_name
        super().__init__(service_name=f"tool_{name}", enabled=enabled)
        self._name = name
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    @property
    def description(self) -> str:
        return self._description

    @property
    @abstractmethod
    def schema(self) -> Dict[str, Any]:
        """Returns the JSON schema for tool arguments."""
        pass

    @abstractmethod
    async def _execute_tool(self, **kwargs: Any) -> Any:
        """
        Internal execution logic to be implemented by subclasses.
        """
        pass

    async def execute(self, **kwargs: Any) -> Any:
        """
        Public execution entry point with observability and error handling.
        """
        if not self.is_ready():
            # If the tool relies on external connections, it must be started first.
            # For simple function tools, _connect is a no-op, so they are ready immediately after start().
            self.logger.warning(
                f"Tool '{self.name}' executed while not in READY state."
            )

        with self.tracer.start_as_current_span(
            f"tool.execution.{self.name}", kind=SpanKind.INTERNAL
        ) as span:
            span.set_attribute("tool.name", self.name)
            # Log keys only to avoid PII leakage in traces without sanitization
            span.set_attribute("tool.args_keys", list(kwargs.keys()))

            try:
                self.logger.debug(f"Executing tool '{self.name}'")
                result = await self._execute_tool(**kwargs)

                span.set_status(StatusCode.OK)
                return result

            except Exception as e:
                self.logger.error(f"Tool '{self.name}' execution failed: {e}")
                span.record_exception(e)
                span.set_status(StatusCode.ERROR, description=str(e))
                raise ToolExecutionError(self.name, e) from e

    # --- Lifecycle Hooks (BaseService Template Methods) ---

    async def _connect(self) -> None:
        """
        Default connection logic.
        Override this if the tool needs to connect to a DB or API.
        """
        pass

    async def _close(self) -> None:
        """
        Default cleanup logic.
        Override this to close sessions/connections.
        """
        pass
