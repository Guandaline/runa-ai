# tests/integration/nala/api/observability/test_int_metric_scheduler.py
import asyncio
from unittest.mock import AsyncMock

import pytest

# Import the new Factory and the Protocol
from nala.athomic.observability.metrics import MetricProbe, MetricSchedulerFactory
from nala.athomic.observability.metrics.probes import probe_registry


# A simple mock probe for the test that explicitly implements the protocol
class FakeProbe(MetricProbe):
    def __init__(self):
        self.update_mock = AsyncMock()

    async def update(self):
        await self.update_mock()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_metric_scheduler_executes_update():
    """
    Tests if the MetricScheduler correctly finds probes in the registry
    and periodically calls their update() method.
    """
    # ARRANGE
    fake_probe = FakeProbe()
    probe_registry.register("fake_probe", fake_probe)

    scheduler = MetricSchedulerFactory.create()
    scheduler._interval = 0.05

    scheduler_task = None
    try:
        # ACT
        scheduler_task = asyncio.create_task(scheduler.start())
        await scheduler.wait_ready()

        await asyncio.sleep(0.12)

    finally:
        # TEARDOWN
        if scheduler and scheduler.is_running():
            await scheduler.stop()
        if scheduler_task and not scheduler_task.done():
            scheduler_task.cancel()
            await asyncio.gather(scheduler_task, return_exceptions=True)

    # ASSERT
    assert (
        fake_probe.update_mock.await_count >= 2
    ), f"Probe was called {fake_probe.update_mock.await_count} times, expected at least 2."
