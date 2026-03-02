# /tests/integration/nala/athomic/conftest.py

import asyncio
import uuid
from typing import Any, Dict, Optional, Tuple
from uuid import uuid4

import pytest
import pytest_asyncio


global_received_payloads_store: Dict[str, Any] = {}
global_event_received_flags: Dict[str, asyncio.Event] = {}


@pytest.fixture
def run_id() -> str:
    """Provides a short, unique ID for a test run to ensure topic name isolation."""
    return uuid.uuid4().hex[:8]


@pytest.fixture(scope="function")
def test_topic_and_group(run_id: Optional[str] = None) -> Tuple[str, str]:
    """Generates a unique topic name and group name for a test."""
    run_id = run_id or uuid4()
    topic = f"test.topic.fixture.{run_id}"
    group = f"test.group.fixture.{run_id}"
    return topic, group


@pytest_asyncio.fixture()
def get_environment_variables() -> Any:
    delay_seconds = 1
    test_run_id = uuid4()
    delay_topic_name = f"__nala_delay_1s_{test_run_id}"
    final_topic_name = f"final_topic_{test_run_id}"
    group_id = f"test-e2e-consumer-group-{test_run_id}"
    delay_group_id = f"delay-consumer-group-{test_run_id}"

    return (
        delay_seconds,
        test_run_id,
        delay_topic_name,
        final_topic_name,
        group_id,
        delay_group_id,
    )
