import asyncio
import logging
import os
import time
from collections.abc import AsyncGenerator
from typing import ClassVar, List
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
import redis
from dotenv import load_dotenv

from nala.athomic.config.schemas.resilience.retry_config import RetrySettings
from nala.athomic.config.settings import get_settings
from nala.athomic.performance import install_uvloop_if_available
from nala.athomic.services.protocol import BaseServiceProtocol


@pytest.fixture(scope="session", autouse=True)
def setup_uvloop_for_tests():
    """
    Session-scoped fixture to conditionally install uvloop at the beginning of the test run.

    It only installs uvloop if the environment variable 'NALA_FORCE_UVLOOP' is set to 'true' or '1'.
    'autouse=True' ensures it runs automatically for every test session.
    """
    # Check for an environment variable to decide whether to install uvloop
    force_uvloop = os.getenv("NALA_FORCE_UVLOOP", "true").lower() in (
        "true",
        "1",
        "yes",
    )

    if force_uvloop:
        install_uvloop_if_available()
    else:
        # Using a simple print because the logger might not be configured yet.
        print(
            "INFO:     NALA_FORCE_UVLOOP not set. Using the default asyncio event loop for tests."
        )
    yield


load_dotenv(".env")


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests",
    )

    parser.addoption(
        "--run-ai",
        action="store_true",
        default=False,
        help="run slow ai integration tests",
    )


def pytest_configure(config):
    config.addinivalue_line("markers", "integration: mark a test as integration")
    config.addinivalue_line("markers", "ai: mark test as ai integration test")


def pytest_collection_modifyitems(config, items):
    run_integration = os.getenv("RUN_INTEGRATION_TESTS", "false").lower() in (
        "1",
        "true",
        "yes",
    )
    for item in items:
        if "integration" in item.keywords and not run_integration:
            item.add_marker(
                pytest.mark.skip(reason="RUN_INTEGRATION_TESTS is not enabled")
            )

    if config.getoption("--run-ai"):
        # If the flag IS present, do not skip anything based on this rule
        return

    # If the flag is NOT present, skip tests marked with 'ai'
    skip_ai = pytest.mark.skip(reason="need --run-ai option to run")

    for item in items:
        if "ai" in item.keywords and "integration" in item.keywords:
            item.add_marker(skip_ai)


@pytest.fixture(autouse=True)
def clear_settings_cache_automatically():
    """
    Fixture automatically executed before EACH test.
    Clears the cache of the get_settings() function to ensure that each test
    loads the configuration based on its own environment/fixtures.
    """
    get_settings.cache_clear()


class AsyncIterator:
    def __init__(self, async_gen):
        self._gen = async_gen

    def __aiter__(self):
        return self

    async def __anext__(self):
        return await self._gen.__anext__()


@pytest.fixture
def mock_redis_client() -> AsyncMock:
    """
    Fixture (shared via conftest) for a mock of the
    redis.asyncio.Redis client.
    """
    client = AsyncMock(spec=redis.Redis)

    mock_lock_obj = AsyncMock()
    client.lock = MagicMock(return_value=mock_lock_obj)

    client.setnx = AsyncMock(return_value=1)
    client.get = AsyncMock(
        return_value=str(int(time.time()) - 10).encode()
    )  # Returns bytes
    client.getset = AsyncMock(return_value=str(int(time.time()) + 60).encode())
    client.delete = AsyncMock(return_value=1)

    return client


@pytest.fixture
def mock_lock_object(mock_redis_client) -> AsyncMock:
    """
    Fixture (shared via conftest) that returns the mock lock object
    returned by mock_redis_client.lock().
    Allows configuring/verifying __aenter__ and __aexit__ in tests.
    """
    lock_obj = mock_redis_client.lock.return_value
    # Ensure context manager methods are AsyncMocks
    lock_obj.__aenter__ = AsyncMock(return_value=None)
    lock_obj.__aexit__ = AsyncMock(return_value=None)
    return lock_obj


class PropagateHandler(logging.Handler):
    def emit(self, record):
        logging.getLogger(record.name).handle(record)


@pytest.fixture(autouse=True)
async def check_no_pending_tasks():
    yield
    # Wait for the next loop to ensure tasks are finished
    await asyncio.sleep(0)
    # Get all live tasks (except itself)
    pending = [
        t for t in asyncio.all_tasks() if not t.done() and t != asyncio.current_task()
    ]
    if pending:
        print("WARNING: Pending tasks after test:", pending)
        # Cancel all to avoid warnings when closing the loop
        for t in pending:
            t.cancel()
        await asyncio.gather(*pending, return_exceptions=True)


@pytest.fixture()
def get_secrets_config():
    token = "root"
    addr = os.getenv("VAULT_ADDR_TEST", "http://localhost:8200")
    return addr, token


@pytest.fixture(scope="session", autouse=True)
def mock_global_settings_for_imports():
    """
    Globally mocks get_settings during test collection to prevent ImportError
    when modules using AppSettings are imported at module level.
    """
    with patch("nala.athomic.config.get_settings") as mock_get_settings:
        mock_settings = MagicMock()

        mock_settings.resilience.retry = RetrySettings(
            attempts=1,  # A safe default value for import time
            wait_min_seconds=0.001,
            wait_max_seconds=0.001,
        )

        mock_get_settings.return_value = mock_settings
        yield


@pytest.fixture(autouse=True)
def clear_settings_cache():
    """
    Fixture that automatically runs for every test to ensure a fresh
    settings load by clearing the internal cache.
    """
    try:
        # Try to access and clear the internal cache of the settings module
        app_settings = get_settings()
        if hasattr(app_settings, "_settings_cache"):
            app_settings._settings_cache.clear()
    except Exception:
        # If the cache structure changes in the future, this test will not break.
        pass
    yield


class ServiceManager:
    """
    Handles the startup of services for a test.
    The cleanup (teardown) is managed by the pytest fixture
    that creates and yields this instance.
    """

    _service_tasks: ClassVar[List[asyncio.Task]]
    _services_to_manage: ClassVar[List[BaseServiceProtocol]]

    def __init__(
        self,
        service_tasks: List[asyncio.Task],
        services_to_manage: List[BaseServiceProtocol],
    ):
        """
        Instantiated by the service_lifecycle_manager fixture.
        """
        self._service_tasks = service_tasks
        self._services_to_manage = services_to_manage

    async def start_services(self, services: List[BaseServiceProtocol]):
        """
        Starts the given list of services, waits for them to be ready,
        and registers them for cleanup by the fixture.
        """
        # Filter out None entries if services are conditionally created
        valid_services = [s for s in services if s]

        if not valid_services:
            return

        # Append to the lists managed by the fixture's closure
        self._services_to_manage.extend(valid_services)

        new_tasks = [asyncio.create_task(s.start()) for s in valid_services]
        self._service_tasks.extend(new_tasks)

        # Wait for all services to report ready
        await asyncio.gather(*(s.wait_ready() for s in valid_services))


@pytest_asyncio.fixture(scope="function")
async def service_lifecycle_manager() -> AsyncGenerator[ServiceManager, None]:
    """
    Yields a ServiceManager instance and handles the graceful shutdown
    of all services started via that instance.
    """

    service_tasks: List[asyncio.Task] = []
    services_to_manage: List[BaseServiceProtocol] = []

    # Yield the manager instance, injecting the lists
    try:
        yield ServiceManager(
            service_tasks=service_tasks, services_to_manage=services_to_manage
        )
    finally:
        # This is the cleanup (teardown) phase, managed by the fixture
        if services_to_manage:
            await asyncio.gather(
                *(s.stop() for s in services_to_manage if s.is_running()),
                return_exceptions=True,
            )

        for task in service_tasks:
            if not task.done():
                task.cancel()

        if service_tasks:
            await asyncio.gather(*service_tasks, return_exceptions=True)
