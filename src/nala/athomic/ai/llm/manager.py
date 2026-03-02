from typing import Optional

from nala.athomic.ai.governance.guards.factory import GuardFactory
from nala.athomic.ai.governance.pipeline import GuardPipeline
from nala.athomic.ai.llm.base import BaseLLM
from nala.athomic.ai.llm.factory import LLMFactory
from nala.athomic.base.base_manager import BaseManager
from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai import AISettings
from nala.athomic.config.schemas.ai.llm import LLMConnectionSettings


class LLMManager(BaseManager[BaseLLM, LLMConnectionSettings]):
    """
    A specialized lifecycle manager for LLM (Large Language Model) connections.

    This class orchestrates the initialization, connection, and shutdown of
    multiple LLM providers (e.g., 'openai_default', 'vertex_flash'). It acts
    as the single point of access for retrieving specific LLM clients within
    the application.

    It inherits robust lifecycle management from `BaseManager`, ensuring that
    all configured LLM connections are established during startup and
    gracefully closed during shutdown.
    """

    def __init__(self, settings: Optional[AISettings] = None):
        """
        Initializes the LLMManager.

        Args:
            settings: The root AI settings object. If None, loads from global settings.
        """
        ai_settings = settings or get_settings().ai

        super().__init__(
            service_name="llm_manager",
            settings=ai_settings.connections,
        )
        self.factory = LLMFactory
        self.guard_pipeline: GuardPipeline = GuardFactory.create(ai_settings.governance)

    async def before_start(self) -> None:
        """
        Overrides BaseManager.before_start to compose LLM instances with Guardrails.
        """
        self.logger.debug(f"[{self.service_name}] Clearing existing client lists.")
        self._managed_clients.clear()
        self.managed_services.clear()

        if not self.factory:
            raise NotImplementedError(
                f"Manager '{self.service_name}' did not set 'self.factory' in its __init__."
            )

        client_settings = self._resolve_active_configs()

        if not client_settings:
            self.logger.info(f"No active connections found for '{self.service_name}'.")
            return

        for settings in client_settings:
            connection_name = getattr(settings, "connection_name")
            self.logger.debug(
                f"Creating client for connection: '{connection_name}' using {self.factory.__name__}"
            )

            # Use LLMFactory to create the *base* provider instance
            base_instance: BaseLLM = self.factory.create(settings=settings)

            base_instance.guards = self.guard_pipeline.input_guards
            base_instance.output_guards = self.guard_pipeline.output_guards

            is_default = connection_name == self.settings.default_connection_name
            if is_default:
                self.logger.debug(
                    f"Connection '{connection_name}' set as default for {self.service_name}."
                )

            self._register_client(name=connection_name, instance=base_instance)


# Singleton Instance
llm_manager = LLMManager()
