from typing import Any, Dict, Optional

from opentelemetry.trace import Span, SpanKind, StatusCode

from nala.athomic.observability.tracing import get_tracer
from nala.athomic.observability.tracing.attributes import AI_SYSTEM


class AgentTracing:
    """
    Manages the integration between AI Agent lifecycle events and OpenTelemetry tracing.

    This class acts as a centralized instrumentor to automatically generate spans
    for agent runs, tool executions, and chain steps, ensuring visibility into
    the cognitive architecture.
    """

    def __init__(self, tracer_name: str = "nala.ai.agent") -> None:
        """
        Initializes the tracing handler with a dedicated tracer.

        Args:
            tracer_name: The name scope for the OpenTelemetry tracer.
        """
        self._tracer = get_tracer(tracer_name)
        self._active_spans: Dict[str, Span] = {}

    def on_agent_start(
        self,
        run_id: str,
        agent_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """
        Starts a new span representing the beginning of an agent execution.

        Args:
            run_id: Unique identifier for the execution run.
            agent_name: Name of the agent being executed.
            metadata: Additional metadata to attach to the span.
        """
        span_name = f"Agent Run: {agent_name}"
        attributes = {
            "agent.name": agent_name,
            "agent.run_id": run_id,
            AI_SYSTEM: "nala_agent_engine",
        }

        if metadata:
            for key, value in metadata.items():
                if value is not None:
                    attributes[f"agent.metadata.{key}"] = str(value)

        span = self._tracer.start_span(
            name=span_name,
            kind=SpanKind.INTERNAL,
            attributes=attributes,
        )

        self._active_spans[run_id] = span

    def on_tool_start(
        self,
        run_id: str,
        tool_name: str,
        tool_input: str,
        parent_run_id: Optional[str] = None,
    ) -> None:
        """
        Starts a child span for a specific tool execution within the agent.

        Args:
            run_id: Unique identifier for the tool execution.
            tool_name: Name of the tool being invoked.
            tool_input: The input payload sent to the tool.
            parent_run_id: The run_id of the agent triggering this tool.
        """
        span_name = f"Tool Execution: {tool_name}"
        attributes = {
            "tool.name": tool_name,
            "tool.input": tool_input,
            "agent.run_id": run_id,
        }

        if parent_run_id:
            attributes["agent.parent_run_id"] = parent_run_id

        # Note: In a real distributed context, we would extract the parent context
        # from the parent_run_id if active in the same process.
        span = self._tracer.start_span(
            name=span_name,
            kind=SpanKind.CLIENT,
            attributes=attributes,
        )
        self._active_spans[run_id] = span

    def on_run_end(self, run_id: str, outputs: Optional[Dict[str, Any]] = None) -> None:
        """
        Finalizes the execution span (Agent or Tool), recording outputs and setting status to OK.

        Args:
            run_id: Unique identifier for the execution run.
            outputs: The final output dictionary.
        """
        span = self._active_spans.pop(run_id, None)
        if span:
            if outputs:
                for key, value in outputs.items():
                    # Limit output size to prevent span explosion
                    span.set_attribute(f"output.{key}", str(value)[:1024])

            span.set_status(StatusCode.OK)
            span.end()

    def on_run_error(self, run_id: str, error: Exception) -> None:
        """
        Finalizes the execution span with an error status.

        Args:
            run_id: Unique identifier for the execution run.
            error: The exception raised during execution.
        """
        span = self._active_spans.pop(run_id, None)
        if span:
            span.record_exception(error)
            span.set_status(StatusCode.ERROR, str(error))
            span.end()
