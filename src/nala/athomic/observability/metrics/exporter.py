# src/nala/athomic/observability/metrics/start_server.py
from prometheus_client import start_http_server

from nala.athomic.config import get_settings
from nala.athomic.observability.log import get_logger

logger = get_logger(__name__)


def start_metrics_server() -> None:
    """
    Initializes and starts the HTTP server to expose Prometheus metrics
    for scraping by external monitoring systems.

    This operation is conditional and runs only if observability is enabled
    in the application settings.
    """
    settings = get_settings().observability

    if settings.enabled:
        port = settings.exporter_port
        logger.info(f"Starting metrics server on port {port}")
        # prometheus_client's start_http_server is synchronous and non-blocking
        start_http_server(port)
        logger.success("Metrics server started successfully.")
    else:
        logger.info(
            "Observability is disabled via settings. Skipping metrics server startup."
        )
