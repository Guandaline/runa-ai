# Context & Token Management

## Overview

The **Context Module** (`nala.athomic.ai.context`) provides centralized intelligence for managing Large Language Model (LLM) context windows.
Instead of hardcoding limits (e.g., "always fetch 5 documents"), this module calculates a **Dynamic Token Budget** for every transaction based on:

1.  **Physical Model Limits**: Automatically resolved via Regex patterns (e.g., `gpt-4-turbo` has 128k, `llama3` has 8k).
2.  **Business Policies**: Dynamic caps based on user tiers (e.g., "Free Tier" gets 4k tokens, "Pro" gets 32k).
3.  **Safety Margins**: Reserves buffers for system prompts and output generation.

### Key Features

-   **Model Registry**: Regex-based resolution of model capabilities. No need to update code when new model versions (e.g., `gpt-4-0613`) are released.
-   **Policy Engine**: Pluggable strategies (`TokenLimitPolicy`) to enforce quotas.
-   **Tokenizer Abstraction**: Wraps `tiktoken` to ensure accurate counting across different encodings (`cl100k_base`, etc.).
-   **Budget Calculator**: Provides a precise count of *remaining* tokens available for context injection.

---

## Architecture

The core component is the `TokenService`, usually accessed via the `TokenServiceFactory`.

1.  **Resolution**: The service receives a model name (e.g., `gpt-4-turbo`). It queries the `ModelContextRegistry` to find the physical hard limit.
2.  **Policy Application**: It runs a chain of policies (e.g., `TierBasedLimitPolicy`) which may lower the effective limit based on the current `ExecutionContext` (User Role/Tenant).
3.  **Budgeting**: It subtracts the System Prompt, User Query, and Reserved Output tokens from the Effective Limit.
4.  **Result**: Returns a `TokenBudget` object containing `available_context_tokens`.

---

## Usage Example

### Calculating a Budget

```python
from nala.athomic.ai.context.factory import TokenServiceFactory

# 1. Initialize Service
token_service = TokenServiceFactory.create()

# 2. Calculate Budget
budget = token_service.calculate_budget(
    model_name="gpt-4-turbo",
    system_prompt="You are a helpful assistant.",
    user_query="Analyze this large document.",
    max_output_tokens=500
)

print(f"Physical Limit: {budget.model_limit}")     # 128,000
print(f"Effective Limit: {budget.effective_limit}") # e.g., 8,000 (if capped by policy)
print(f"Available for RAG: {budget.available_context_tokens}") 
```

### Counting Tokens

```python
count = token_service.count_tokens("Hello World", encoding_name="cl100k_base")
```

---

## Configuration

Context rules are configured under `[ai.context]` in `settings.toml`.

```toml
[default.ai.context]
enabled = true
default_model_limit = 4096
default_encoding = "cl100k_base"
default_safety_margin = 0.05 # Reserve 5% of the window for safety

  # --- Physical Model Rules (Regex) ---
  # Order matters: First match wins.
  
  [[default.ai.context.model_rules]]
  pattern = "^gpt-4-(turbo|o|1106|0125).*"
  context_window = 128000
  encoding_name = "cl100k_base"

  [[default.ai.context.model_rules]]
  pattern = "^gpt-4.*"
  context_window = 8192
  encoding_name = "cl100k_base"
  
  [[default.ai.context.model_rules]]
  pattern = "^llama3.*"
  context_window = 8192
  encoding_name = "cl100k_base"
```

---

## Policies

### TierBasedLimitPolicy

Restricts the context window based on the user's role found in `context_vars.get_role()`.

**Configuration (Injected via Factory):**
```python
policy = TierBasedLimitPolicy(
    tier_limits={
        "free": 4096,
        "pro": 32000,
        "enterprise": 128000
    }
)
```

---

## API Reference

::: nala.athomic.ai.context.manager.TokenService

::: nala.athomic.ai.context.registry.ModelContextRegistry

::: nala.athomic.ai.context.policies.TierBasedLimitPolicy

::: nala.athomic.ai.schemas.tokens.TokenBudget