# tests/integration/nala/athomic/resilience/circuit_breaker/test_int_multiple_circuits.py
from importlib import reload
from typing import AsyncGenerator

import pytest
import redis.asyncio as redis
from aiobreaker import CircuitBreakerError

from nala.athomic.config import settings as settings_module
from nala.athomic.resilience.circuit_breaker import (
    CircuitBreakerFactory,
    circuit_breaker,
)

pytestmark = [pytest.mark.integration, pytest.mark.asyncio]


@pytest.fixture(scope="function", autouse=True)
def isolated_settings_for_test(monkeypatch):
    """
    Loads test-specific settings for this module and ensures a clean factory state.
    """
    monkeypatch.setenv(
        "NALA_SETTINGS_FILES",
        "tests/settings/resilience/test_int_multiple_circuits.toml",
    )
    reload(settings_module)
    CircuitBreakerFactory.clear_cache()
    yield
    reload(settings_module)
    CircuitBreakerFactory.clear_cache()


@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[redis.Redis, None]:
    """
    Provides a direct redis client to inspect state and ensures a clean DB.
    """
    client = redis.from_url("redis://localhost:6379/11", decode_responses=True)
    try:
        await client.ping()
    except Exception as e:
        pytest.skip(f"Redis not reachable at redis://localhost:6379/11: {e}")

    await client.flushdb()
    yield client
    await client.flushdb()
    await client.aclose()


async def test_multiple_circuits_operate_independently(redis_client: redis.Redis):
    """
    Verifies that two separate circuits operate independently, ensuring that
    a failure in one does not affect the other. This validates the storage
    key namespacing provided by PatchedCircuitRedisStorage.
    """
    # ARRANGE
    service_a_breaker_name = "service_a_breaker"
    service_b_breaker_name = "service_b_breaker"  # This will use default settings
    fail_max_for_a = 2  # As defined in the .toml file

    @circuit_breaker(name=service_a_breaker_name)
    async def call_service_a():
        raise ValueError("Service A is down")

    @circuit_breaker(name=service_b_breaker_name)
    async def call_service_b():
        return "Service B is OK"

    # ACT 1: Trip the circuit for Service A
    # The first n-1 calls will raise the original exception
    for _ in range(fail_max_for_a - 1):
        with pytest.raises(ValueError, match="Service A is down"):
            await call_service_a()

    with pytest.raises(CircuitBreakerError):
        await call_service_a()

    # ASSERT 1: Circuit A is open, but Circuit B remains operational
    # Verify Service A's circuit is now open and blocking calls
    with pytest.raises(CircuitBreakerError):
        await call_service_a()

    # The crucial assertion: verify Service B is unaffected
    result_b = await call_service_b()
    assert result_b == "Service B is OK"

    # Verify states directly in Redis for full confidence
    state_a = await redis_client.get(
        f"test_int_multi_cb:{service_a_breaker_name}:state"
    )
    state_b = await redis_client.get(
        f"test_int_multi_cb:{service_b_breaker_name}:state"
    )
    assert state_a == "OPEN"
    # State B is never called with a failure, so the key might not even exist,
    # or it will be CLOSED if it was ever successfully called.
    assert state_b in [None, "CLOSED"]
