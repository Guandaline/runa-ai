# Health & Readiness Checks

## Overview

The Health & Readiness module provides a standardized and extensible system for determining if the application is healthy and ready to handle traffic. This is a critical feature for running in orchestrated environments like Kubernetes, which rely on readiness probes to know when to add a service instance to the load balancer.

The framework exposes an HTTP endpoint, typically `/readyz`, which runs a series of checks against all critical dependencies (databases, message brokers, external APIs) and reports their status.

---

## How It Works

The system is built around a few core components that promote decoupling and extensibility:

1.  **`ReadinessCheck` Protocol**: A simple contract that any readiness check must follow. It requires a unique `name`, an `enabled()` method, and an asynchronous `check()` method that returns `True` for healthy or `False` for unhealthy.

2.  **`ReadinessRegistry`**: A singleton registry where all readiness check instances are registered during application startup.

3.  **`ServiceReadinessCheck`**: A generic and powerful implementation that can check the status of any Athomic `BaseService`. It automatically integrates with the service lifecycle, so a readiness check for the Kafka consumer, for example, simply queries `kafka_consumer.is_ready()`.

4.  **`/readyz` Endpoint**: An internal API route that, when called, executes the `run_all()` method on the `ReadinessRegistry`. This runs all registered checks concurrently and aggregates their results into a single JSON response. The overall HTTP status will be `200 OK` only if all enabled checks pass.

---

## How to Add a Custom Readiness Check

You can easily add your own application-specific readiness checks. For example, you might want to check the status of a critical third-party API that your service depends on.

### 1. Create the Check Class

Create a class that implements the `ReadinessCheck` protocol.

```python
# In your_app/health_checks.py
from nala.athomic.http import HttpClientFactory
from nala.athomic.observability.health import ReadinessCheck

class ExternalApiServiceCheck(ReadinessCheck):
    name = "external_api_status"

    def __init__(self):
        # Get a pre-configured HTTP client from the factory
        self.http_client = HttpClientFactory.create("my_external_api_client")

    def enabled(self) -> bool:
        # The check is enabled if the client itself is enabled in the config
        return self.http_client.is_enabled()

    async def check(self) -> bool:
        try:
            # Perform a lightweight check, like a HEAD request or a health endpoint call
            response = await self.http_client.get("/_health")
            return response.status_code == 200
        except Exception:
            return False
```

### 2. Register the Check

In your application's startup sequence (e.g., `domain_initializers.py`), instantiate your check and register it.

```python
# In your_app/startup/domain_initializers.py
from nala.athomic.observability.health import readiness_registry
from your_app.health_checks import ExternalApiServiceCheck

def register_domain_services():
    # ... other registrations ...
    
    # Register your custom health check
    readiness_registry.register(ExternalApiServiceCheck())
```

Your custom check will now be automatically executed and reported by the `/readyz` endpoint.

---

## Example Response

A call to the `/readyz` endpoint will return a JSON response detailing the status of each check.

```json
{
  "status": "unhealthy",
  "checks": {
    "consul_client": "ok",
    "database_connection_manager": "ok",
    "kafka_consumer_my_app.events.v1": "ok",
    "external_api_status": "fail"
  }
}
```

---

## API Reference

::: nala.athomic.observability.health.protocol.ReadinessCheck

::: nala.athomic.observability.health.registry.ReadinessRegistry

::: nala.athomic.observability.health.checks.service_check.ServiceReadinessCheck