# src/nala/athomic/ai/agents/persistence/registry.py
from typing import Type

from nala.athomic.ai.agents.persistence.protocol import CheckpointProtocol
from nala.athomic.base.registry import BaseRegistry


class CheckpointRegistry(BaseRegistry[Type[CheckpointProtocol]]):
    """
    Registry for Agent Persistence Checkpoint Provider Classes.

    It maps a strategy name (e.g., 'kv_store') to the concrete class
    implementation. The Factory is responsible for instantiating these classes
    and resolving their specific dependencies.
    """

    def register_defaults(self) -> None:
        """Registers the default strategies."""
        # Local import to prevent circular dependencies during module loading
        from nala.athomic.ai.agents.persistence.providers.kv import KVCheckpoint

        self.register("kv_store", KVCheckpoint)

# Singleton instance
checkpoint_registry = CheckpointRegistry(protocol=CheckpointProtocol)
