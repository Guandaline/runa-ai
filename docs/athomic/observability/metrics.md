# Metrics

## Overview

The metrics module provides deep, out-of-the-box application monitoring using the **Prometheus** format, the de-facto standard for cloud-native observability. Nearly every component in the Athomic Layer is instrumented with detailed metrics, offering invaluable insights into performance, throughput, error rates, and overall system health.

This allows you to create powerful dashboards and alerts to monitor your application in real-time.

### How It Works

1.  **Metric Registration**: Throughout the Athomic codebase, Prometheus metrics (`Counter`, `Histogram`, `Gauge`) are defined to track specific events and states.
2.  **Instrumentation**: Core components automatically update these metrics during their operation. For example, the `HttpClient` updates a histogram with request latency and a counter for successes or failures.
3.  **Exposure**: At startup, the application automatically starts a lightweight HTTP server that exposes a `/metrics` endpoint. This endpoint serves all registered metrics in the text-based Prometheus format.
4.  **Scraping**: A Prometheus server is then configured to periodically "scrape" (fetch) the data from this `/metrics` endpoint, storing it as a time series.

### The `MetricScheduler`

For metrics that cannot be updated on-event (like the current number of pending messages), Athomic includes a `MetricScheduler`. This is a background service that periodically runs "Probes" (`MetricProbe` implementations) to collect and update gauge-based metrics, such as Kafka consumer lag.

---

## Built-in Metrics

Athomic provides a comprehensive set of built-in metrics. Below is a high-level summary of what is available out-of-the-box. For a full list, you can inspect the `/metrics` endpoint of a running application.

-   **API Layer**:
    -   Request rate, error rate, and latency (per route, method, and status code).
    -   Number of in-progress requests.
-   **Database & Cache**:
    -   Operation latency and total counts for each KV store and document database operation (`get`, `set`, `find_by_id`, etc.).
    -   Cache hit and miss ratios.
-   **Messaging (Kafka)**:
    -   Number of messages published and consumed.
    -   Message publishing latency.
    -   **Consumer Lag** per topic and partition.
    -   Total messages sent to the Dead Letter Queue (DLQ).
-   **Resilience Patterns**:
    -   **Circuit Breaker**: State changes, failures recorded, and calls blocked.
    -   **Retry**: Total retry attempts and permanent failures.
    -   **Rate Limiter**: Total requests allowed and blocked per policy.
    -   **Bulkhead**: Concurrently executing requests and rejections.
-   **Transactional Outbox**:
    -   Number of events processed (success/failure).
    -   Event processing lag (time between creation and publication).
    -   Pending messages for the "hottest" aggregate keys.

---

## Adding Custom Metrics

You can easily define and use your own custom metrics within your application's business logic using the `prometheus-client` library.

```python
from prometheus_client import Counter
from nala.athomic.observability import get_logger

logger = get_logger(__name__)

# 1. Define your metric at the module level.
ORDERS_PROCESSED_TOTAL = Counter(
    "orders_processed_total",
    "Total number of orders processed.",
    ["order_type", "status"]
)

class OrderService:
    async def process_order(self, order: Order):
        try:
            # ... your business logic ...
            
            # 2. Increment the counter on success.
            ORDERS_PROCESSED_TOTAL.labels(order_type=order.type, status="success").inc()
            logger.info("Order processed successfully.")
            
        except Exception:
            # 3. Increment the counter with a different label on failure.
            ORDERS_PROCESSED_TOTAL.labels(order_type=order.type, status="failure").inc()
            logger.error("Failed to process order.")
            raise
```

---

## Configuration

Metrics are configured under the `[observability]` and `[observability.metrics]` sections in your `settings.toml`.

```toml
[default.observability]
enabled = true

# If true, starts an HTTP server to expose Prometheus metrics.
exporter_enabled = true

# The port on which the Prometheus metrics server will listen.
exporter_port = 9100

  [default.observability.metrics]
  enabled = true

  # The interval in seconds at which the MetricScheduler runs its probes (e.g., for Kafka lag).
  collection_interval_seconds = 60
  
  # If true, access to the /metrics endpoint is restricted to the IPs below.
  metrics_protection_enabled = false
  allow_metrics_ips = ["127.0.0.1", "10.0.0.5"]
```

---

## API Reference

::: nala.athomic.observability.metrics.exporter.start_metrics_server

::: nala.athomic.observability.metrics.metric_scheduler.MetricScheduler

::: nala.athomic.observability.metrics.protocol.MetricProbe