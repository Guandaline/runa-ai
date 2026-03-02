import asyncio
import importlib
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio

from nala.api.startup.domain_initializers import register_api_domain_initializers
from nala.athomic.config import get_settings
from nala.athomic.database.manager import ConnectionManager
from nala.athomic.facade import Athomic
from nala.athomic.lifecycle import get_lifecycle_registry
from nala.athomic.observability.metrics.factory import MetricSchedulerFactory

pytestmark = pytest.mark.integration


async def force_cleanup_registry() -> None:
    """
    Iterates through the Lifecycle Registry and forcefully stops all running services.
    Obliterates the global state across all known singleton factories to ensure a
    sterile environment for each test execution.
    """
    registry = get_lifecycle_registry()
    services = list(registry.all().items())

    for service_name, service_instance in reversed(services):
        if hasattr(service_instance, "is_running") and service_instance.is_running():
            try:
                await service_instance.stop()
            except Exception:
                pass

    await asyncio.sleep(0.1)

    get_settings.cache_clear()
    registry.clear()

    from nala.athomic.database.factory import connection_manager_factory

    if hasattr(connection_manager_factory, "clear"):
        connection_manager_factory.clear()

    if hasattr(MetricSchedulerFactory, "clear"):
        MetricSchedulerFactory.clear()
    if hasattr(MetricSchedulerFactory, "create") and hasattr(
        MetricSchedulerFactory.create, "cache_clear"
    ):
        MetricSchedulerFactory.create.cache_clear()
    if hasattr(MetricSchedulerFactory, "_instance"):
        MetricSchedulerFactory._instance = None


@pytest_asyncio.fixture(scope="function")
async def athomic_facade(
    monkeypatch: pytest.MonkeyPatch,
) -> AsyncGenerator[Athomic, None]:
    """
    Handles the complete setup and teardown for an Athomic integration test.
    """
    await force_cleanup_registry()

    from nala.athomic.config import settings as settings_module

    monkeypatch.setenv(
        "NALA_SETTINGS_FILES",
        "tests/settings/lifecycle/test_int_athomic_startup.toml",
    )
    monkeypatch.setenv("ENV_FOR_DYNACONF", "default")

    importlib.reload(settings_module)
    test_settings = get_settings()

    athomic = Athomic(
        settings=test_settings,
        domain_initializers_registrar=register_api_domain_initializers,
    )
    await athomic.startup()

    yield athomic

    await athomic.shutdown()
    await force_cleanup_registry()


@pytest.mark.asyncio
async def test_athomic_startup_with_local_services(athomic_facade: Athomic) -> None:
    """
    Tests if the facade starts all local services correctly and if they are operational.
    """
    registry = get_lifecycle_registry()

    connection_manager: ConnectionManager = registry.get("database_connection_manager")

    assert (
        connection_manager and connection_manager.is_ready()
    ), "Connection Manager did not start."

    kvstore_client = connection_manager.get_kv_store("default_local")

    assert kvstore_client and kvstore_client.is_ready(), "KVStore client did not start."

    test_key = "integration-test-key"
    test_value = "it-works"

    await kvstore_client.set(test_key, test_value)
    retrieved_value = await kvstore_client.get(test_key)

    assert (
        retrieved_value == test_value
    ), "The operation on the in-memory KVStore failed."
