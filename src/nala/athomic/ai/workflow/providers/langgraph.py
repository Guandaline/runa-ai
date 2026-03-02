from typing import Any, Dict, Optional, cast

from langgraph.graph import StateGraph

from nala.athomic.ai.workflow.base import BaseWorkflowEngine
from nala.athomic.ai.workflow.definition.structure import WorkflowDefinition
from nala.athomic.ai.workflow.exceptions import (
    WorkflowDefinitionError,
    WorkflowError,
)
from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)


class LangGraphWorkflowEngine(BaseWorkflowEngine):
    """
    Adapter for the LangGraph execution engine.

    Translates the platform-agnostic WorkflowDefinition into a LangGraph StateGraph.
    Enables capabilities like:
    - Cyclic graphs (Loops)
    - LangSmith integration (Automatic Tracing)
    - Persistence (Checkpointers - future integration)
    """

    def __init__(
        self,
        settings: WorkflowSettings,
        service_name: str = "langgraph_workflow_engine",
    ) -> None:
        super().__init__(settings=settings, service_name=service_name)

    def _compile_impl(self, definition: WorkflowDefinition) -> Any:
        """
        Converts the generic definition into a LangGraph CompiledGraph.
        """
        builder = StateGraph(Dict[str, Any])

        for name, handler in definition.steps.items():
            builder.add_node(name, handler)

        for source, dest in definition.routes:
            builder.add_edge(source, dest)

        for route in definition.conditional_routes:
            builder.add_conditional_edges(
                route.source,
                route.condition_fn,
                route.destinations,
            )

        if not definition.entry_point:
            raise WorkflowDefinitionError("Workflow has no entry point defined.")

        builder.set_entry_point(definition.entry_point)

        try:
            return builder.compile()
        except Exception as e:
            raise WorkflowDefinitionError(f"LangGraph compilation failed: {e}") from e

    async def _run_impl(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the compiled LangGraph.
        """
        graph = self._compiled_workflow
        run_config = config or {}

        recursion_limit = self.settings.max_execution_steps

        lg_config = {
            "recursion_limit": recursion_limit,
            "configurable": run_config,
        }

        if "thread_id" in run_config:
            lg_config["configurable"]["thread_id"] = run_config["thread_id"]

        try:
            final_state = await graph.ainvoke(input_data, config=lg_config)
            return cast(Dict[str, Any], final_state)

        except Exception as e:
            error_msg = str(e).lower()
            if "recursion limit" in error_msg or "recursionlimit" in error_msg:
                raise WorkflowError(
                    f"Max execution steps ({recursion_limit}) exceeded."
                ) from e
            raise
