# src/nala/athomic/resilience/circuit_breaker/patched_storage.py
from typing import Any, Optional

from aiobreaker.state import CircuitBreakerState
from aiobreaker.storage.redis import CircuitRedisStorage


class PatchedCircuitRedisStorage(CircuitRedisStorage):
    """
    A patched version of `CircuitRedisStorage` designed to fix implementation
    issues in the base library related to distributed state management.

    It ensures:
    1. **Unique Keys:** Each circuit instance uses a unique, namespaced key in Redis.
    2. **Correct State Handling:** Ensures that state is retrieved and stored as
       the correct `CircuitBreakerState` enum member.
    """

    def __init__(
        self,
        circuit_name: str,
        initial_state: CircuitBreakerState,
        namespace: Optional[str] = None,
        redis_object: Optional[Any] = None,
    ):
        """
        Initializes the patched storage with explicit arguments.

        Args:
            circuit_name (str): The unique name for this circuit, used to build Redis keys
                                to ensure isolation between different circuit breakers.
            initial_state (CircuitBreakerState): The initial state enum member for the circuit.
            namespace (Optional[str]): The global namespace prefix for all circuit keys.
            redis_object (Optional[Any]): The synchronous redis client instance
                                         (from `redis` library).
        """
        self._circuit_name = circuit_name
        self._namespace_str = namespace

        # Calls the parent constructor, which initializes the Redis connection object
        super().__init__(
            state=initial_state, redis_object=redis_object, namespace=namespace
        )

    def _namespace(self, key: str) -> str:
        """
        Overrides the parent method to build a uniquely namespaced Redis key.

        The final key format is: `[namespace]:[circuit_name]:[key]`

        Args:
            key (str): The suffix key (e.g., 'state', 'fail_counter').

        Returns:
            str: The full, unique key string for Redis.
        """
        if self._namespace_str:
            return f"{self._namespace_str}:{self._circuit_name}:{key}"
        return f"{self._circuit_name}:{key}"

    @property
    def state(self) -> CircuitBreakerState:
        """
        Overrides the parent property to retrieve the current state from Redis
        and return it as a validated `CircuitBreakerState` enum member.
        """
        state_name_bytes = self._redis.get(self._namespace("state"))

        if state_name_bytes:
            state_name = state_name_bytes.decode("utf-8")
            try:
                return CircuitBreakerState[state_name]
            except KeyError:
                # Fallback to initial state if an unknown state is found in Redis
                return self._initial_state

        # If the key does not exist in Redis, return the configured initial state
        return self._initial_state

    @state.setter
    def state(self, new_state: CircuitBreakerState) -> None:
        """
        Saves the new state of the circuit to Redis using the enum's string name.

        Args:
            new_state (CircuitBreakerState): The new state enum member to persist.
        """
        # Persists the state using the enum's name (e.g., 'OPEN', 'CLOSED')
        self._redis.set(self._namespace("state"), new_state.name)
