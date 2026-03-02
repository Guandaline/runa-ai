import time
from typing import Any, Dict, Optional

from nala.athomic.ai.workflow.base import BaseWorkflowEngine
from nala.athomic.ai.workflow.definition.structure import WorkflowDefinition
from nala.athomic.ai.workflow.exceptions import (
    NodeExecutionError,
    WorkflowDefinitionError,
    WorkflowError,
)
from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)
from nala.athomic.observability.metrics.usage.ai.workflow_metrics import (
    workflow_step_duration_seconds,
    workflow_step_errors_total,
    workflow_steps_count,
)


class InMemoryWorkflowEngine(BaseWorkflowEngine):
    """
    A pure Python implementation of the Workflow Engine.

    This provider executes workflows in-memory without external dependencies.
    It is suitable for:
    1. Unit testing workflow definitions.
    2. Simple, stateless linear or cyclic flows.
    3. Debugging graph logic.

    It enforces the 'max_execution_steps' limit defined in WorkflowSettings
    to prevent infinite loops in cyclic graphs.
    """

    def __init__(
        self,
        settings: WorkflowSettings,
        service_name: str = "memory_workflow_engine",
    ) -> None:
        super().__init__(settings=settings, service_name=service_name)

    def _compile_impl(self, definition: WorkflowDefinition) -> WorkflowDefinition:
        """
        Validates the workflow definition structure.
        Since this is an in-memory engine, 'compilation' is just validation.
        """
        # 1. Validate Entry Point
        if not definition.entry_point:
            raise WorkflowDefinitionError("Workflow has no entry point defined.")

        if definition.entry_point not in definition.steps:
            raise WorkflowDefinitionError(
                f"Entry point '{definition.entry_point}' not found in steps."
            )

        # 2. Validate Routes (Static)
        for source, dest in definition.routes:
            if source not in definition.steps:
                raise WorkflowDefinitionError(
                    f"Route source '{source}' not found in steps."
                )
            if dest not in definition.steps:
                raise WorkflowDefinitionError(
                    f"Route destination '{dest}' not found in steps."
                )

        # 3. Validate Conditional Routes
        for route in definition.conditional_routes:
            if route.source not in definition.steps:
                raise WorkflowDefinitionError(
                    f"Conditional route source '{route.source}' not found in steps."
                )

        return definition

    async def _run_impl(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the workflow graph in a linear loop using the inherited self.settings.
        """
        definition: WorkflowDefinition = self._compiled_workflow
        state = input_data.copy()
        current_step_name = definition.entry_point

        # Runtime Config
        workflow_name = config.get("workflow_name", "unknown") if config else "unknown"
        step_count = 0
        max_steps = self.settings.max_execution_steps

        self.logger.debug(f"Starting in-memory execution at '{current_step_name}'")

        while current_step_name is not None:
            # 1. Safety Check (Infinite Loop Protection)
            self._check_max_steps(step_count, max_steps)

            step_handler = definition.steps.get(current_step_name)
            if not step_handler:
                raise WorkflowError(
                    f"Step '{current_step_name}' logic not found during execution."
                )

            # 2. Execute Node with Telemetry
            await self._execute_step(
                step_handler, state, current_step_name, workflow_name
            )
            step_count += 1

            # 3. Determine Next Step (Routing Logic)
            next_step = self._resolve_next_step(definition, current_step_name, state)

            if next_step and self.settings.debug_mode:
                self.logger.debug(f"Transitioning: {current_step_name} -> {next_step}")

            current_step_name = next_step

        # Metrics: Total Steps
        workflow_steps_count.labels(workflow_name=workflow_name).observe(step_count)

        return state

    def _check_max_steps(self, step_count: int, max_steps: int) -> None:
        """Check if the workflow has exceeded the maximum execution steps."""
        if step_count >= max_steps:
            msg = (
                f"Workflow exceeded maximum execution steps ({max_steps}). "
                "Check for infinite loops or increase the limit."
            )
            self.logger.error(msg)
            raise WorkflowError(msg)

    async def _execute_step(
        self,
        step_handler: Any,
        state: Dict[str, Any],
        current_step_name: str,
        workflow_name: str,
    ) -> None:
        """Execute a single step with telemetry and error handling."""
        start_time = time.perf_counter()
        try:
            if self.settings.debug_mode:
                self.logger.debug(f"Executing step: {current_step_name}")

            # Support both async and sync handlers
            if hasattr(step_handler, "execute"):
                updates = await step_handler.execute(state)
            else:
                # Fallback for simple callables/functions
                updates = await step_handler(state)

            if updates:
                state.update(updates)

            step_duration = time.perf_counter() - start_time

            # Metrics: Step Success
            workflow_step_duration_seconds.labels(
                workflow_name=workflow_name,
                step_name=current_step_name,
                status="success",
            ).observe(step_duration)

        except Exception as e:
            # Metrics: Step Failure
            workflow_step_errors_total.labels(
                workflow_name=workflow_name,
                step_name=current_step_name,
                error_type=type(e).__name__,
            ).inc()

            self.logger.error(
                f"Error in step '{current_step_name}': {e}", exc_info=True
            )
            raise NodeExecutionError(current_step_name, e) from e

    def _resolve_next_step(
        self,
        definition: WorkflowDefinition,
        current_node: str,
        state: Dict[str, Any],
    ) -> Optional[str]:
        """
        Determines the next node based on conditional and static routes.
        Priority: Conditional > Static.
        """
        # A. Check Conditional Routes
        for route in definition.conditional_routes:
            if route.source == current_node:
                try:
                    # Evaluate condition
                    condition_result = route.condition_fn(state)
                    # Map result to next node
                    if condition_result in route.destinations:
                        return route.destinations[condition_result]
                    else:
                        self.logger.warning(
                            f"Condition returned '{condition_result}' but no mapping found in destinations."
                        )
                except Exception as e:
                    raise NodeExecutionError(
                        current_node, f"Failed to evaluate condition: {e}"
                    ) from e

        # B. Check Static Routes
        for source, dest in definition.routes:
            if source == current_node:
                return dest

        # C. End of Workflow
        return None
