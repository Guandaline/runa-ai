from typing import Any

from nala.athomic.base.factory import FactoryProtocol
from nala.athomic.config.schemas.ai.workflow.workflow_settings import (
    WorkflowSettings,
)

from .protocol import WorkflowEngineProtocol
from .registry import workflow_registry


class WorkflowEngineFactory(FactoryProtocol[WorkflowEngineProtocol, WorkflowSettings]):
    """
    Factory for creating configured Workflow Engine instances.

    It consults the 'workflow_registry' to locate the implementation class
    specified in 'WorkflowSettings.default_provider' and instantiates it.
    """

    @classmethod
    def create(
        cls, settings: WorkflowSettings, **kwargs: Any
    ) -> WorkflowEngineProtocol:
        """
        Creates a new instance of a Workflow Engine based on settings.

        Args:
            settings: The workflow configuration object containing the
                      default provider name (e.g., 'memory', 'langgraph').
            **kwargs: Additional arguments passed to the engine constructor
                      (e.g., service_name).

        Returns:
            An initialized and configured WorkflowEngineProtocol instance.

        Raises:
            ValueError: If the configured provider is not registered.
        """
        provider_name = settings.default_provider

        # The registry handles the lookup and raises ValueError if not found
        engine_class = workflow_registry.get(provider_name)

        # BaseWorkflowEngine expects (settings, service_name)
        # We ensure service_name is handled if not passed in kwargs
        if "service_name" not in kwargs:
            kwargs["service_name"] = f"{provider_name}_workflow_engine"

        return engine_class(settings=settings, **kwargs)
