# Large Language Models (LLM)

## Overview

The `athomic.ai.llm` module provides a unified, provider-agnostic interface for interacting with Large Language Models (LLMs) such as OpenAI (GPT-4) and Google Vertex AI (Gemini).
It is designed to solve common challenges in production AI applications:

-   **Vendor Lock-in**: Switch providers via configuration without changing code.
-   **Real-Time Streaming**: Native support for asynchronous token streaming with standardized chunks.
-   **Structured Data**: Reliably extract Pydantic models from LLM outputs using a standardized API (`generate_structured`).
-   **Observability**: Automatic tracing (OpenTelemetry) and metrics (Prometheus) for every call (unary or streaming).
-   **Embedded Governance**: Enforce rate limits and safety checks directly within the provider pipeline.

---

## Core Concepts

### `LLMProviderProtocol`

The contract that all LLM providers must implement. It defines three primary operations:

-   `generate_content(prompt, ...)`: Generates unstructured text (blocking).
-   `stream_content(prompt, ...)`: Generates unstructured text incrementally (async iterator).
-   `generate_structured(prompt, response_model, ...)`: Generates a structured object adhering to a specific Pydantic schema.

### `BaseLLM` & Governance

The abstract base class now handles **AI Governance** automatically:
1.  **Input Guards**: Executed *before* the request is sent to the provider. These are blocking (e.g., Rate Limiting, Prompt Injection check).
2.  **Output Guards**: Executed *after* the response is received. For streaming, these currently act in audit mode.

---

## Usage Example

### Basic Text Generation (Blocking)

```python
from nala.athomic.ai.llm.factory import LLMFactory
from nala.athomic.config import get_settings

async def chat_with_ai(user_input: str):
    # 1. Create the provider from global settings
    settings = get_settings().ai.llm.connections["default"]
    llm = LLMFactory.create(settings)

    # 2. Generate content (waits for full completion)
    response = await llm.generate_content(
        prompt=user_input,
        system_message="You are a helpful assistant."
    )
    return response.content
```

### Real-Time Streaming

```python
import sys
from nala.athomic.ai.llm.factory import LLMFactory

async def stream_chat(user_input: str):
    llm = LLMFactory.create_default()

    # stream_content yields LLMResponseChunk objects
    async for chunk in llm.stream_content(prompt=user_input):
        
        # 1. Process incremental text (Token Delta)
        if chunk.content_delta:
            sys.stdout.write(chunk.content_delta)
            sys.stdout.flush()
            
        # 2. Handle metadata on finish (Usage, Stop Reason)
        if chunk.is_final:
            print(f"n[Meta] Finished. Tokens: {chunk.usage.total_tokens}")
```

### Structured Output (JSON Extraction)

```python
from pydantic import BaseModel, Field
from nala.athomic.ai.llm.factory import LLMFactory

class UserIntent(BaseModel):
    intent: str = Field(..., description="The user's intention (buy, sell, support)")
    confidence: float

async def analyze_intent(text: str):
    llm = LLMFactory.create_default()

    # Guaranteed to return a UserIntent instance or raise StructuredOutputError
    intent: UserIntent = await llm.generate_structured(
        prompt=f"Analyze this text: {text}",
        response_model=UserIntent
    )
    
    return intent
```

---

## Configuration

LLM connections are configured in `settings.toml`.

```toml
[default.ai.llm]
# The default connection to use
default_connection_name = "gpt4_main"

  [default.ai.llm.connections.gpt4_main]
  backend = "openai"
  default_model = "gpt-4-turbo"
  timeout = 30.0
  
    [default.ai.llm.connections.gpt4_main.provider]
    # OpenAI specific settings
    api_key = { path = "ai/openai", key = "api_key" }
    organization_id = "org-123"
```

---

## API Reference

::: nala.athomic.ai.llm.protocol.LLMProviderProtocol

::: nala.athomic.ai.llm.base.BaseLLM

::: nala.athomic.ai.schemas.llms.LLMResponseChunk

::: nala.athomic.ai.llm.factory.LLMFactory