# Distributed Tracing

## Overview

The distributed tracing module provides end-to-end request tracing capabilities built on the **OpenTelemetry** standard, the industry benchmark for observability. This feature is invaluable for debugging performance bottlenecks and understanding complex, asynchronous workflows in a microservices architecture.

It allows you to visualize the entire journey of a request as it travels through different services and components—from the initial API call, through message brokers, to database queries and back.

### Key Features

-   **OpenTelemetry Native**: Fully compliant with the OpenTelemetry standard, allowing integration with any OTLP-compatible backend (e.g., Jaeger, Datadog, Honeycomb).
-   **Auto-Instrumentation**: Automatically creates trace spans for common I/O operations, including outgoing HTTP requests (`httpx`), database queries (`pymongo`), and cache interactions (`redis`).
-   **Effortless Manual Instrumentation**: A simple `@with_observability` decorator allows you to add detailed tracing to your business logic with a single line of code.
-   **Automatic Context Propagation**: The trace context (e.g., `trace_id`, `span_id`) is automatically propagated across service boundaries, including HTTP calls and messages sent via a broker like Kafka.

---

## How It Works

### Setup

During application startup, the `setup_tracing()` function is automatically called. It configures the global OpenTelemetry SDK, initializes an OTLP exporter to send trace data to a collector, and applies auto-instrumentation patches to key libraries.

### Instrumentation

-   **Automatic**: For libraries like `httpx` and `pymongo`, you get tracing for free. Every database query or external API call will appear as a span in your trace without you writing any extra code.
-   **Manual**: For your own business logic, you should use the provided decorators to create spans that represent meaningful units of work.

---

## Usage: The `@with_observability` Decorator

The easiest and recommended way to add tracing to your code is with the `@with_observability` decorator. It's a powerful tool that automatically handles the entire span lifecycle.

When you decorate a function, it will:
1.  Start a new span when the function is called.
2.  Automatically add useful attributes to the span, such as the function's arguments.
3.  Measure the execution duration.
4.  Record any exceptions that occur.
5.  Set the span's final status (`OK` or `ERROR`).

#### Example

```python
from nala.athomic.observability.decorators import with_observability

class UserProfileService:
    @with_observability(
        name="service.get_user_profile",
        attributes_from_args={"user_id": "user.id"}
    )
    async def get_profile(self, user_id: str) -> dict:
        # ... your business logic ...
        profile_data = await self.repository.find_by_id(user_id)
        # ... more logic ...
        return profile_data
```
In this example, every call to `get_profile` will generate a trace span named `"service.get_user_profile"`, and it will automatically include an attribute `user.id` with the value of the `user_id` argument.

---

## Context Propagation

Athomic handles trace context propagation automatically across service boundaries:

-   **HTTP Requests**: The `HttpClient` automatically injects W3C Trace Context headers into outgoing requests. The API middleware automatically extracts them from incoming requests, ensuring the trace continues seamlessly.
-   **Messaging**: When a message is published, the `Producer` injects the trace context into the message headers. The `Consumer` on the other side extracts it, allowing a single trace to span from an API request to a background worker processing a resulting message.

---

## Configuration

Tracing is configured under the `[observability]` section in your `settings.toml`.

```toml
[default.observability]
# A master switch for all observability features (metrics and tracing).
enabled = true

# A master switch specifically for distributed tracing.
tracing_enabled = true

# The gRPC or HTTP endpoint of the OpenTelemetry Collector.
# Spans will be sent here.
# Example for a local Jaeger setup:
otlp_endpoint = "http://localhost:4317"

# The sampling rate for traces (1.0 = 100%, 0.5 = 50%).
sampling_rate = 1.0

# Optional: Override the service name that appears in your tracing backend.
# If not set, it defaults to the `app_name`.
service_name_override = "my-awesome-service"
```

---

## API Reference

::: nala.athomic.observability.tracing.setup_tracing

::: nala.athomic.observability.decorators.with_observability

::: nala.athomic.observability.get_tracer
