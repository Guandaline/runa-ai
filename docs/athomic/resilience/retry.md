# Retry

## Overview

The Retry pattern is a fundamental resilience mechanism that allows an application to automatically re-execute an operation that has failed due to a transient error, such as a temporary network glitch or a brief service unavailability. This prevents temporary issues from escalating into hard failures, significantly improving the stability and reliability of your service.

The Athomic retry module is built on the robust and battle-tested `tenacity` library. It provides a highly configurable, policy-based approach to retries through a simple `@retry` decorator.

### Key Features

-   **Declarative Use**: Apply complex retry logic with a single decorator.
-   **Policy-Based Configuration**: Centrally define multiple named retry policies (e.g., "fast_retry", "slow_retry") in your configuration files.
-   **Exponential Backoff & Jitter**: Built-in support for exponential backoff with random jitter to prevent "thundering herd" problems.
-   **Live Configuration**: Retry policies can be tuned and updated at runtime without restarting the application.
-   **Full Observability**: Every retry attempt is logged and instrumented with traces and metrics.

---

## How It Works

The retry mechanism is centered around **Retry Policies**. A policy is a set of rules that defines the retry behavior:

-   **`attempts`**: The maximum number of times to retry the operation.
-   **`wait_min_seconds` / `wait_max_seconds`**: The minimum and maximum delay between retries.
-   **`backoff`**: A multiplier for the delay, enabling exponential backoff.
-   **`jitter`**: A random factor added to the delay to de-synchronize retries from multiple clients.
-   **`exceptions`**: A list of specific exception types that should trigger a retry.

The `@retry` decorator applies a policy to a function. When the decorated function is called, a `RetryHandler` manages the execution. If the function raises one of the configured exceptions, the handler waits for the calculated delay and then re-executes the function, up to the maximum number of attempts.

---

## Usage Example

You can apply a named retry policy directly to any asynchronous function.

```python
from nala.athomic.resilience import retry, RetryFactory

# In a real app, the factory would be a singleton.
retry_factory = RetryFactory()
# Get a pre-configured policy from your settings.toml
fast_retry_policy = retry_factory.create_policy(name="fast_retry")

@retry(policy=fast_retry_policy)
async def call_flaky_service(request_data: dict) -> dict:
    """
    This function will be retried up to 3 times with a short,
    exponential backoff if it fails with an HTTPException.
    """
    # This call might fail temporarily
    response = await http_client.post("/external-api", json=request_data)
    response.raise_for_status()
    return response.json()
```

---

## Configuration

You define all your retry policies in `settings.toml` under the `[resilience.retry]` section. You can specify a `default_policy` and a dictionary of named `policies` for different use cases.

```toml
[default.resilience.retry]
enabled = true

  # This policy will be used if no specific policy is requested.
  [default.resilience.retry.default_policy]
  attempts = 3
  wait_min_seconds = 1.0
  wait_max_seconds = 10.0
  backoff = 2.0 # Wait time will be ~1s, 2s, 4s...
  exceptions = ["HTTPRequestError", "HTTPTimeoutError"]

  # A dictionary of named, reusable policies.
  [default.resilience.retry.policies]
    
    # A policy for quick, internal retries.
    [default.resilience.retry.policies.fast_retry]
    attempts = 3
    wait_min_seconds = 0.1
    wait_max_seconds = 1.0
    backoff = 1.5
    exceptions = ["HTTPException"]

    # A policy for long-running background tasks.
    [default.resilience.retry.policies.long_retry]
    attempts = 10
    wait_min_seconds = 5.0
    wait_max_seconds = 300.0 # 5 minutes
    backoff = 2.0
    exceptions = ["ConnectionError"]
```

### Live Configuration

Because the `RetrySettings` model is a `LiveConfigModel`, you can change any of these values (e.g., `attempts`, `wait_max_seconds`) in your live configuration source (like Consul), and the `RetryFactory` will use the new values for all subsequent operations without requiring an application restart.

---

## API Reference

::: nala.athomic.resilience.retry.decorator.retry

::: nala.athomic.resilience.retry.policy.RetryPolicy

::: nala.athomic.resilience.retry.factory.RetryFactory

::: nala.athomic.resilience.retry.handler.RetryHandler