# Structured Logging

## Overview

The logging module provides a powerful, structured, and secure logging system built upon the `Loguru` library. It is designed to be both highly performant and developer-friendly, with two primary goals:

1.  **Rich, Structured Logs**: Automatically enriches log records with contextual information from the `Context` module (e.g., `request_id`, `tenant_id`, `trace_id`). It can output logs as JSON, making them easy to parse, index, and query in modern log management systems.
2.  **Security by Default**: Includes a robust and extensible sensitive data masking engine that automatically redacts PII (Personally Identifiable Information) and secrets from log messages *before* they are written to any sink.

---

## How to Use

Getting a logger instance is simple. The `get_logger()` function returns a pre-configured singleton instance of the Loguru logger.

```python
from nala.athomic.observability import get_logger

# It's recommended to get a logger scoped to your module
logger = get_logger(__name__)

def process_user_data(user_id: str):
    # This log record will be automatically enriched with any
    # context variables that are currently set.
    logger.info(f"Processing data for user {user_id}")
```

---

## Sensitive Data Masking

This is a core security feature of the Athomic Layer. The `SensitiveDataFilter` automatically finds and redacts sensitive information from log messages before they are written.

### Out-of-the-Box Patterns

The filter comes with a wide range of built-in patterns for common PII and secrets, including:

-   **JWTs**: Replaces JSON Web Tokens with `***REDACTED_JWT***`.
-   **Credit Card Numbers**: Performs PCI-compliant masking, showing only the last four digits (e.g., `****-****-****-1234`).
-   **Brazilian CPFs**: Performs smart masking, showing only the verification digits (e.g., `***.***.***-56`).
-   **Phone Numbers**: Performs smart masking, preserving the area code and last two digits (e.g., `(11) *****-**78`).
-   **Email Addresses**: Replaces emails with `***@***.***`.
-   **Common Secret Keys**: Redacts values for keys like `"password"`, `"api_key"`, and `"token"` in JSON-like strings.
-   **Authorization Headers**: Redacts the token from `Authorization: Bearer ...` headers.

### Pattern Scoring System

To ensure accuracy, the filter applies masking patterns in order of specificity. A highly specific pattern for a JWT will run before a more generic pattern for an email address, preventing incorrect redactions.

### Adding Custom Masking Patterns

You can easily extend the masker with your own regex patterns directly in your configuration file.

```toml
# In settings.toml
[default.logging]
# ... other logging settings ...

[[default.logging.sensitive_patterns]]
# This will find any string matching "secret-project-key-..." and redact it.
regex = "secret-project-key-[a-zA-Z0-9]+"
replacement = "REDACTED_PROJECT_KEY"

[[default.logging.sensitive_patterns]]
# You can also use regex capture groups.
regex = "user_phone_number=(d+)"
replacement = "user_phone_number=REDACTED"
```

---

## JSON Logging

For production environments, it is highly recommended to enable JSON logging. This formats every log entry as a structured JSON object, which can be easily ingested and indexed by platforms like Elasticsearch (ELK Stack), Datadog, Splunk, or Google Cloud Logging.

To enable it, simply set `serialize = true` in your configuration.

---

## Configuration

The logging system is configured under the `[logging]` section in your `settings.toml`.

```toml
[default.logging]
# The minimum log level to process (e.g., "DEBUG", "INFO", "WARNING").
level = "INFO"

# If true, log records are formatted as JSON strings.
serialize = true

# If true, logs are written to a file instead of the console.
log_to_file = false
log_file_path = ".logs/app.log"
rotation = "100 MB"
retention = "7 days"

# A list of custom patterns for the sensitive data filter.
[[default.logging.sensitive_patterns]]
regex = "my-custom-secret-([a-z0-9-]+)"
replacement = "my-custom-secret-REDACTED"
```

---

## API Reference

::: nala.athomic.observability.get_logger

::: nala.athomic.observability.log.filters.sensitive_data_filter.SensitiveDataFilter

::: nala.athomic.observability.log.maskers.base_masker.BaseMasker