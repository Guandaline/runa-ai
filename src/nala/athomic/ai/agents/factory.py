# src/nala/athomic/ai/agents/factory.py
from typing import Optional

from nala.athomic.ai.agents.executors.strategies.sync import SyncToolExecutor
from nala.athomic.ai.agents.persistence.factory import CheckpointFactory
from nala.athomic.ai.agents.persistence.protocol import CheckpointProtocol
from nala.athomic.ai.agents.service import AgentService
from nala.athomic.ai.llm.manager import LLMManager, llm_manager
from nala.athomic.ai.tools.registry import tool_registry
from nala.athomic.config import get_settings
from nala.athomic.config.schemas.ai.agents import AgentProfileSettings, AgentsSettings
from nala.athomic.observability import get_logger

logger = get_logger(__name__)


class AgentFactory:
    """
    Factory responsible for creating fully configured AgentService instances.

    Delegates LLM resolution to the central LLMManager and orchestrates the
    creation of Tool Executors and Persistence Checkpointers based on the
    application configuration.
    """

    @classmethod
    def create(
        cls,
        profile_name: Optional[str] = None,
        thread_id: Optional[str] = None,
        settings: Optional[AgentsSettings] = None,
        llm_manager_instance: Optional[LLMManager] = llm_manager,
    ) -> AgentService:
        """
        Creates a new AgentService instance based on the specified profile.

        Args:
            profile_name: The name of the agent profile to load from settings.
                          Defaults to the application's default profile if None.
            thread_id: Optional session identifier. If provided, state persistence
                       will be enabled for this agent instance (if configured globally).

        Returns:
            A configured and ready-to-use AgentService instance.

        Raises:
            RuntimeError: If agents are disabled or dependencies (LLM) cannot be resolved.
            ValueError: If the requested profile does not exist.
        """

        agents_settings: AgentsSettings = settings or get_settings().ai.agents

        if not agents_settings or not agents_settings.enabled:
            raise RuntimeError("Agents module is disabled in application settings.")

        target_profile_name = profile_name or agents_settings.default_profile

        profile: Optional[AgentProfileSettings] = (
            agents_settings.profiles.connections.get(target_profile_name)
        )

        if not profile:
            available = list(agents_settings.profiles.connections.keys())
            raise ValueError(
                f"Agent profile '{target_profile_name}' not found. "
                f"Available profiles: {available}"
            )

        if not profile.enabled:
            raise RuntimeError(f"Agent profile '{target_profile_name}' is disabled.")

        logger.debug(f"Creating agent service for profile: '{target_profile_name}'")

        # 1. Resolve LLM Connection
        connection_name = (
            profile.connection_name or agents_settings.default_connection_name
        )
        try:
            base_llm = llm_manager_instance.get_client(name=connection_name)
            llm_instance = base_llm

        except (KeyError, RuntimeError) as e:
            raise RuntimeError(
                f"Failed to initialize Agent '{profile.name}'. "
                f"The required LLM connection '{connection_name}' could not be retrieved from LLMManager. "
                f"Reason: {e}. "
                "Ensure LLMManager is connected and the connection is defined/enabled in settings."
            ) from e

        # 2. Resolve Persistence (Optional)
        checkpointer: Optional[CheckpointProtocol] = None

        # Access persistence settings dynamically to support partial configurations
        # Assuming app_settings.ai.agents.persistence structure
        persistence_settings = getattr(agents_settings, "persistence", None)

        if persistence_settings and persistence_settings.enabled and thread_id:
            try:
                checkpointer = CheckpointFactory.create(persistence_settings)
                logger.debug(
                    "Persistence enabled for agent '{}' on thread '{}'. Strategy: {}",
                    target_profile_name,
                    thread_id,
                    persistence_settings.strategy,
                )
            except Exception as e:
                logger.error(
                    "Failed to initialize Persistence for agent '{}': {}. "
                    "Agent will run in volatile mode.",
                    target_profile_name,
                    e,
                )

        # 3. Resolve Tool Executor
        executor = SyncToolExecutor(tool_registry=tool_registry)

        # 4. Instantiate Service
        service = AgentService(
            settings=profile,
            llm=llm_instance,
            executor=executor,
            checkpointer=checkpointer,
            thread_id=thread_id,
        )

        logger.info(f"AgentService '{service.service_name}' created successfully.")
        return service
