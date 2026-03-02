# src/nala/athomic/ai/agents/persistence/protocol.py
from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class CheckpointProtocol(Protocol):
    """
    Protocol defining the interface for Agent State Persistence Providers.

    Providers are responsible for the low-level storage and retrieval of
    serialized state data, agnostic of the backend technology.
    """

    async def save(self, thread_id: str, state: Dict[str, Any]) -> None:
        """
        Persists the agent state for a given thread.

        Args:
            thread_id: Unique identifier for the conversation/thread.
            state: The serialized state dictionary to store.
        """
        ...

    async def load(self, thread_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves the latest state for a given thread.

        Args:
            thread_id: Unique identifier for the conversation/thread.

        Returns:
            The serialized state dictionary if found, otherwise None.
        """
        ...

    async def delete(self, thread_id: str) -> None:
        """
        Removes the state for a specific thread (e.g., cleanup).
        """
        ...
