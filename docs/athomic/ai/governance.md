# AI Governance (Guardrails)

## Overview

The AI Governance module, often referred to as "Guardrails," is responsible for enforcing security, compliance, and operational policies when interacting with Large Language Models (LLMs).
Its main purpose is to decouple policy enforcement from specific LLM providers (e.g., OpenAI, Gemini), centralizing the logic in a robust and extensible pipeline.

---

## Integration

The `GuardPipeline` is now integrated directly into the **`BaseLLM`**. This ensures that governance is applied consistently regardless of whether the LLM is called via `LLMManager`, `AgentService`, or `RAGService`.

### Execution Flow

1.  **Input Guards (Blocking)**:
    -   Run synchronously *before* `generate` or `stream_content`.
    -   If a guard fails (e.g., Blocklist, Rate Limit), the operation is aborted immediately, and a `GovernanceViolationError` is raised.

2.  **Output Guards (Context Dependent)**:
    -   **Unary Calls (`generate`)**: Run after the full response is received. Can modify/redact the response content (e.g., PII Sanitization) before returning it to the caller.
    -   **Streaming Calls (`stream_content`)**: Due to the complexity of sanitizing partial token streams without adding significant latency (buffering), output guards in streaming mode currently operate in **Audit/Pass-through** mode. They log violations but do not block the stream in real-time.

---

## Available Guards

The following governance components are currently implemented and ready for configuration:

| Guard Class | Type | Description |
| :--- | :--- | :--- |
| `RateLimitValidator` | Input | Prevents abuse by limiting the number of calls per client or token. |
| `KeywordBlocklistValidator` | Input | Checks prompts against a configured list of banned terms, raising a violation if found. |
| `RegexPIISanitizer` | Input | Identifies and logs PII data in the prompt for compliance purposes. |
| `OutputPIISanitizer` | Output | Masks or redacts identified PII data in the LLM's final response (Non-streaming only). |

---

## Configuration Example

```yaml
# Settings example for an active configuration
ai_governance:
  enabled: true
  input_policy: "fail_fast" # or "aggregate"
  guards:
    rate_limit:
      enabled: true
      max_calls: 100
    keyword_blocking:
      enabled: true
      keywords: ["banned_term", "policy_violation"]
    pii_sanitization:
      enabled: true
      redact_output: true
```