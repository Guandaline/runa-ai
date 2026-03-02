# Circuit Breaker

## Overview

The Circuit Breaker is a stateful resilience pattern designed to prevent an application from repeatedly attempting to execute an operation that is likely to fail. When a downstream service is struggling, the circuit breaker "opens" to stop sending requests to it, allowing the failing service time to recover and preventing the upstream service from wasting resources.

The Athomic implementation is built on the `aiobreaker` library and is managed by a central `CircuitBreakerService`.

### The Three States

A circuit breaker operates as a state machine with three states:

1.  **`CLOSED`**: This is the normal, healthy state. All calls are allowed to pass through to the protected function. The breaker counts failures, and if the count exceeds a configured threshold (`fail_max`), it transitions to `OPEN`.
2.  **`OPEN`**: In this state, all calls to the protected function are blocked immediately without execution, raising a `CircuitBreakerError`. The breaker remains `OPEN` for a configured duration (`reset_timeout`). After the timeout expires, it transitions to `HALF_OPEN`.
3.  **`HALF_OPEN`**: In this state, the breaker allows a single "probe" call to pass through.
    -   If this single call succeeds, the breaker transitions back to `CLOSED`.
    -   If it fails, the breaker transitions back to `OPEN`, restarting the reset timeout.

---

## How It Works

### `@circuit_breaker` Decorator

The primary way to use the pattern is by applying the `@circuit_breaker` decorator to any asynchronous function that performs a potentially failing operation (like an external API call). You must give each circuit a unique `name`.

```python
from nala.athomic.resilience import circuit_breaker

@circuit_breaker(name="payment_service_api")
async def call_payment_service(payment_data: dict):
    # This call is now protected by the 'payment_service_api' circuit.
    response = await http_client.post("/v1/payments", json=payment_data)
    return response
```

### `CircuitBreakerService`

A singleton `CircuitBreakerService` manages all named circuit breakers in the application. It lazily creates and caches a breaker instance for each unique name, configured according to your settings.

### Distributed State Storage

The state of each circuit breaker (its current state, failure count) must be stored somewhere. Athomic supports two backends:

-   **`local`**: In-memory storage. The state is not shared between service instances and is lost on restart. Ideal for local development and testing.
-   **`redis`**: **(Recommended for production)**. Stores the state in Redis. This allows all instances of your service to share the same circuit state, so if one instance detects a failure, all other instances will also open the circuit for that service.

---

## Configuration

You configure the circuit breaker module under the `[resilience.circuit_breaker]` section in your `settings.toml`. You can define global defaults and then override them for specific, named circuits.

```toml
[default.resilience.circuit_breaker]
enabled = true
namespace = "cb" # A prefix for all keys in the storage backend.

# --- Default settings for all circuits ---
default_fail_max = 5 # Open the circuit after 5 consecutive failures.
default_reset_timeout_sec = 30.0 # Keep the circuit open for 30 seconds.

  # --- Storage Provider ---
  # Use Redis for distributed state in production.
  [default.resilience.circuit_breaker.provider]
  backend = "redis"
    [default.resilience.circuit_breaker.provider.redis]
    # Reuses a KVStore connection configuration.
    uri = "redis://localhost:6379/3"

  # --- Specific Overrides for Named Circuits ---
  # This section is a dictionary of named circuit configurations.
  [default.resilience.circuit_breaker.circuits]
    # Override settings for the circuit named "payment_service_api".
    [default.resilience.circuit_breaker.circuits.payment_service_api]
    fail_max = 3 # More sensitive: open after only 3 failures.
    reset_timeout_sec = 60.0 # Keep open for 60 seconds.
```

### Live Configuration

The settings for individual circuits (under `[resilience.circuit_breaker.circuits]`) can be updated at runtime without an application restart if you are using a live configuration provider like Consul. This allows you to tune the sensitivity of your circuit breakers in response to production incidents.

---

## API Reference

::: nala.athomic.resilience.circuit_breaker.decorator.circuit_breaker

::: nala.athomic.resilience.circuit_breaker.service.CircuitBreakerService

::: nala.athomic.resilience.circuit_breaker.exceptions.CircuitBreakerError