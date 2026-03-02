import time
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)
from nala.athomic.observability.metrics.usage.ai.workflow_metrics import (
    workflow_execution_duration_seconds,
    workflow_executions_total,
)
from nala.athomic.services.base import BaseService
from nala.athomic.services.exceptions import (
    ServiceUnavailableError,
)

from .definition.protocol import WorkflowDefinitionProtocol
from .exceptions import WorkflowError
from .protocol import WorkflowEngineProtocol


class BaseWorkflowEngine(BaseService, WorkflowEngineProtocol, ABC):
    """
    Abstract base class for workflow execution engines, integrated as a managed Service.

    Inheritance:
        - BaseService: Provides lifecycle (connect/close), health checks, metrics,
          and the standard 'self.logger'.
        - WorkflowEngineProtocol: Defines the contract for compiling and running workflows.

    Features:
        - Template Method Pattern for both Lifecycle (_connect, _close) and Execution (_run_impl).
        - Automatic Observability (Prometheus metrics & Tracing).
        - Configuration-driven behavior via WorkflowSettings.
    """

    def __init__(
        self, settings: WorkflowSettings, service_name: str = "workflow_engine"
    ) -> None:
        """
        Initialize the workflow engine service.

        Args:
            settings: Configuration object controlling limits and debug modes.
            service_name: Unique identifier for this service instance.
        """
        super().__init__(service_name=service_name, enabled=settings.enabled)

        self.settings = settings
        self._compiled_workflow: Any = None

    async def _connect(self) -> None:
        """
        Lifecycle Hook: Initializes the engine backend.

        This method is called by BaseService.connect().
        Providers should override this if they need to establish external connections.
        """
        self.logger.debug(f"Initializing {self.__class__.__name__} backend...")

    async def _close(self) -> None:
        """
        Lifecycle Hook: Cleans up engine resources.

        This method is called by BaseService.close().
        """
        self._compiled_workflow = None
        self.logger.debug(f"Shutting down {self.__class__.__name__} backend.")

    def compile(self, definition: WorkflowDefinitionProtocol) -> Any:
        """
        Compiles the blueprint into an executable format.
        Wraps the provider implementation with error handling.
        """
        try:
            if self.settings.debug_mode:
                self.logger.debug("Compiling workflow definition...")

            self._compiled_workflow = self._compile_impl(definition)
            return self._compiled_workflow
        except Exception as e:
            # If it's already a domain error, re-raise it without wrapping
            if isinstance(e, WorkflowError):
                raise

            msg = f"Failed to compile workflow: {str(e)}"
            self.logger.error(msg, exc_info=True)
            raise WorkflowError(msg) from e

    async def run(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Executes the workflow with standard observability wrappers.
        """
        # 1. Readiness Check (Utilizing BaseService state)
        if not self.is_ready():
            # Using ServiceUnavailableError directly to ensure correct instantiation
            raise ServiceUnavailableError(
                f"Service '{self.service_name}' is not ready to run workflows."
            )

        if self._compiled_workflow is None:
            raise WorkflowError("Workflow has not been compiled yet.")

        run_config = config or {}
        workflow_name = run_config.get("workflow_name", "unknown_workflow")

        self.logger.info(
            f"Starting workflow '{workflow_name}'.",
            extra={"input_keys": list(input_data.keys())},
        )

        start_time = time.perf_counter()
        status = "success"

        try:
            # Delegate to the concrete provider
            result = await self._run_impl(input_data, run_config)
            return result

        except Exception as e:
            status = "failure"

            if isinstance(e, WorkflowError):
                raise

            self.logger.critical(
                f"Critical workflow failure in '{workflow_name}': {e}",
                exc_info=True,
            )
            raise WorkflowError(f"Workflow execution failed: {e}") from e

        finally:
            duration = time.perf_counter() - start_time

            # Record Observability Metrics
            workflow_executions_total.labels(
                workflow_name=workflow_name, status=status
            ).inc()

            workflow_execution_duration_seconds.labels(
                workflow_name=workflow_name, status=status
            ).observe(duration)

            if self.settings.debug_mode:
                self.logger.debug(
                    f"Workflow '{workflow_name}' finished in {duration:.4f}s with status: {status}"
                )

    def health_extra(self) -> Dict[str, Any]:
        """
        Adds engine-specific details to the /health endpoint (BaseService hook).
        """
        return {
            "provider": self.settings.default_provider,
            "compiled": self._compiled_workflow is not None,
            "max_steps": self.settings.max_execution_steps,
        }

    # --- Abstract Methods (The "Hooks") ---

    @abstractmethod
    def _compile_impl(self, definition: WorkflowDefinitionProtocol) -> Any:
        pass

    @abstractmethod
    async def _run_impl(
        self,
        input_data: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        pass
