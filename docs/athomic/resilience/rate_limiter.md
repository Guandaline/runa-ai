# Rate Limiter

## Overview

The Rate Limiter is a resilience pattern used to control the frequency of operations, such as API requests or function calls, over a period of time. It is essential for:

-   Protecting downstream services from being overwhelmed.
-   Preventing resource starvation and ensuring fair usage.
-   Enforcing API usage quotas for different clients or user tiers.

The Athomic rate limiter is a flexible, policy-based system that allows you to declaratively apply rate limits to any asynchronous function using the `@rate_limited` decorator.

### Key Features

-   **Policy-Based**: Define named, reusable rate limit policies (e.g., `"100/hour"`, `"10/second"`) in your configuration.
-   **Multiple Backends & Strategies**: Supports multiple provider backends, including a highly flexible one based on the `limits` library that allows for different strategies (e.g., `fixed-window`, `moving-window`).
-   **Context-Aware**: Automatically generates unique keys based on the current context, enabling per-user or per-tenant rate limiting.
-   **Live Configuration**: Rate limit policies can be adjusted at runtime without restarting the application, allowing you to respond to traffic spikes dynamically.
-   **Adaptive Throttling**: Can integrate with an advanced Adaptive Throttling engine to automatically adjust limits based on real-time system health metrics.

---

## How It Works

1.  **Decorator**: You apply the `@rate_limited(policy="...")` decorator to an `async` function.
2.  **`RateLimiterService`**: When the function is called, the decorator invokes the central `RateLimiterService`.
3.  **Key Generation**: The service uses the `ContextKeyGenerator` to create a unique key for the operation based on the policy name, function name, and the current execution context (like `tenant_id` or `user_id`).
4.  **Provider Check**: The service then asks the configured provider (e.g., the `limits` provider) if a request for that key is allowed under the specified rate limit string. If the request is denied, a `RateLimitExceeded` exception is raised.

---

## Available Providers

-   **`limits` Provider**: The default and most flexible provider. It is an adapter for the powerful `limits` library and can be configured to use different storage backends (in-memory for testing, Redis for distributed state) and different algorithms (fixed-window, moving-window).
-   **`redis` Provider**: A lightweight, custom implementation that uses native Redis commands to enforce a simple fixed-window algorithm. It reuses the application's main `KVStore` client.

---

## Usage Example

Applying a rate limit to a function is as simple as adding the decorator.

```python
from nala.athomic.resilience.rate_limiter import rate_limited, RateLimitExceeded

@rate_limited(policy="api_heavy_usage")
async def generate_large_report(user_id: str):
    # This function can now only be called according to the
    # "api_heavy_usage" policy defined in the settings.
    # ...
    pass

async def handle_request(user_id: str):
    try:
        await generate_large_report(user_id)
    except RateLimitExceeded:
        # Handle the case where the user has exceeded their quota
        print("Too many requests, please try again later.")
```

---

## Configuration

You define your rate limiting backend and policies in `settings.toml` under the `[resilience.rate_limiter]` section.

```toml
[default.resilience.rate_limiter]
enabled = true
backend = "limits" # Use the 'limits' library provider

  # --- Default settings for the 'limits' provider ---
  [default.resilience.rate_limiter.provider]
  backend = "limits"
  # Use Redis for distributed state
  storage_backend = "redis"
  redis_storage_uri = "redis://localhost:6379/4"
  # Use a more accurate strategy
  strategy = "moving-window"

  # --- Policy Definitions ---
  # A default limit to apply if no specific policy is requested
  default_policy_limit = "1000/hour"

  # A dictionary of named, reusable policies
  [default.resilience.rate_limiter.policies]
  api_light_usage = "100/minute"
  api_heavy_usage = "10/minute"
  login_attempts = "5/hour"
```

### Live Configuration

Because `RateLimiterSettings` is a `LiveConfigModel`, you can change the limit strings for any policy in your live configuration source (e.g., Consul) and the changes will take effect immediately without a restart. This is extremely useful for mitigating traffic spikes or abuse in real-time.

---

## API Reference

::: nala.athomic.resilience.rate_limiter.decorators.rate_limited

::: nala.athomic.resilience.rate_limiter.service.RateLimiterService

::: nala.athomic.resilience.rate_limiter.protocol.RateLimiterProtocol

::: nala.athomic.resilience.rate_limiter.exceptions.RateLimitExceeded