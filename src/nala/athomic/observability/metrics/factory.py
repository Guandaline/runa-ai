# src/nala/athomic/observability/metrics/factory.py
from typing import Optional

from nala.athomic.config import get_settings
from nala.athomic.config.schemas.observability.metrics.metrics_config import (
    MetricsSettings,
)
from nala.athomic.observability.log import get_logger

from .metric_scheduler import MetricScheduler

logger = get_logger(__name__)


class MetricSchedulerFactory:
    """
    Manages the singleton instance of the MetricScheduler.
    """

    _instance: Optional[MetricScheduler] = None

    @classmethod
    def create(cls, settings: Optional[MetricsSettings] = None) -> MetricScheduler:
        """
        Creates and returns a singleton instance of the MetricScheduler.

        If a settings object is not provided, it will use the global settings.
        """
        if cls._instance is not None:
            logger.warning("Returning existing MetricScheduler instance.")
            return cls._instance

        logger.debug("Creating new MetricScheduler instance.")

        settings: MetricsSettings = settings or get_settings().observability.metrics
        cls._instance = MetricScheduler(
            collection_interval_seconds=settings.collection_interval_seconds
        )

        logger.debug("MetricScheduler singleton instance created.")

        return cls._instance

    @classmethod
    async def clear(cls) -> None:
        """
        Stops the scheduler service if it's running and clears the singleton instance.
        Essential for proper test cleanup.
        """
        if cls._instance is not None:
            if cls._instance.is_running() or cls._instance.is_ready():
                await cls._instance.close()

        cls._instance = None
        logger.debug("MetricScheduler singleton instance cleared.")
