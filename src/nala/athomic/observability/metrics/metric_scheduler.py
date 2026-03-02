# src/nala/athomic/observability/metrics/metric_scheduler.py
import asyncio

from nala.athomic.observability.log import get_logger
from nala.athomic.services.base import BaseService

from .probes.registry import probe_registry

logger = get_logger(__name__)


class MetricScheduler(BaseService):
    """
    Manages a background task responsible for the periodic execution of
    all registered MetricProbes in the central ProbeRegistry.

    This service ensures continuous and asynchronous collection of
    application and infrastructure telemetry.
    """

    def __init__(self, collection_interval_seconds: int):
        """
        Initializes the scheduler with the specified collection interval.

        Args:
            collection_interval_seconds: The frequency (in seconds) at which
                                         the probes should be executed.
        """
        super().__init__(service_name="metric_scheduler")
        self._interval = collection_interval_seconds

    async def _run_loop(self) -> None:
        """
        The main processing loop, executed as a non-blocking background task
        by the BaseService lifecycle management.
        """
        await self.set_ready()

        while self.is_running():
            try:
                # 1. Retrieve all active probes from the registry
                active_probes = probe_registry.all().items()

                self.logger.debug(
                    f"Running collection cycle for {len(active_probes)} probe(s)..."
                )

                # 2. Sequential execution of probes
                for name, probe in active_probes:
                    try:
                        self.logger.debug(
                            f"Executing probe '{name}' ({probe.__class__.__name__})"
                        )
                        # Execute the asynchronous update method
                        await probe.update()
                    except Exception:
                        # Log the specific probe failure but continue to the next one (Resilience)
                        self.logger.exception(
                            f"Error executing probe '{name}' ({probe.__class__.__name__})"
                        )

                # 3. Wait for the next collection interval
                await asyncio.sleep(self._interval)

            except asyncio.CancelledError:
                self.logger.info("MetricScheduler loop cancelled.")
                # Propagate cancellation to stop the background task gracefully
                raise
            except Exception:
                self.logger.exception(
                    "Unexpected error in metric collection loop. Restarting cycle."
                )
                # On unexpected loop error, apply sleep before restarting the cycle (Backoff/Resilience)
                await asyncio.sleep(self._interval)
