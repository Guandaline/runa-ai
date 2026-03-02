# Cognitive Intent Engine

## Overview

The **Cognitive Intent Engine** (`nala.athomic.ai.cognitive`) acts as the "Pre-frontal Cortex" of the AI stack. It is responsible for perceiving and classifying user intent *before* any action is taken (such as calling a tool or querying a database).

Unlike approaches that mix classification logic within Agents or RAG services, this module provides a dedicated layer for **Query Understanding**, enabling smarter and safer routing.

### Key Features

-   **Decoupling**: Separates "Understanding" logic (Cognitive) from "Acting" logic (Agents/RAG).
-   **Provider Pattern**: Agnostic architecture allowing the use of LLMs (via `instructor`) or, in the future, classical ML models (BERT, Random Forest) for classification.
-   **Robust Schema**: Uses Pydantic validation with type coercion to handle the unpredictability of smaller models (e.g., Llama 3.2 via Ollama).
-   **Full Observability**: Automatic metrics for classification latency, intent distribution, and confidence scores.

---

## Architecture

The module follows the **"Provider is Service"** pattern, where the concrete implementation inherits directly from the base service to ensure lifecycle and telemetry consistency.

1.  **Service Layer (`CognitiveBaseService`)**: The abstract class that defines the `classify` contract and manages connection, tracing, and metrics.
2.  **Provider Layer (`LLMCognitiveService`)**: The concrete implementation that uses an `LLMProviderProtocol` to generate structured outputs.
3.  **Data Layer (`IntentClassification`)**: The strict data contract that normalizes the output (Intent, Confidence, Entities).

---

## Usage Example

The service is typically instantiated via `CognitiveFactory` and injected into an orchestrator (like `AgentService`).

```python
from nala.athomic.ai.cognitive.factory import CognitiveFactory
from nala.athomic.ai.schemas.cognitive import UserIntent

async def process_user_message(query: str, history: str):
    # 1. Initialize Service (Reads strategy from settings)
    cognitive_service = CognitiveFactory.create()
    await cognitive_service.connect()

    # 2. Classify Intent
    result = await cognitive_service.classify(
        query=query,
        history_context=history
    )

    print(f"Detected Intent: {result.primary_intent} (Confidence: {result.confidence})")

    # 3. Routing (Branching)
    if result.primary_intent == UserIntent.SEARCH:
        return await run_rag_pipeline(result.rewritten_query)
    
    elif result.primary_intent == UserIntent.TOOL_USE:
        return await run_agent_tools(result.detected_entities)
        
    elif result.primary_intent == UserIntent.ASK:
        return await simple_chat_response(query)
```

---

## Configuration

The module is configured under the `[ai.cognitive]` section in `settings.toml`. It reuses globally defined LLM connections.

```toml
[default.ai.cognitive]
enabled = true
# Classification strategy ("llm" is the current default)
strategy = "llm"

# Model to use (can be a smaller/faster model for low latency)
default_model = "llama3.2:1b"

# Minimum threshold to consider a classification valid
confidence_threshold = 0.5

# Prompt template used (located in the file system)
default_prompt_template = "cognitive/intent_classification"
```

---

## Available Strategies

### LLM Strategy (`llm`)

Uses a Large Language Model to semantically analyze the query. It is the most flexible strategy, capable of extracting complex entities and rewriting malformed queries.

* **Pros**: High accuracy, no prior training needed, easy to tune via prompt.
* **Cons**: Higher latency (depending on the model) and cost per token.

---

## Observability

The service automatically exports the following metrics to Prometheus:

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `cognitive_classification_duration_seconds` | Histogram | `provider`, `strategy` | Latency of the classification process. |
| `cognitive_classification_total` | Counter | `provider`, `status` | Total throughput and error rate. |
| `cognitive_intent_detected_total` | Counter | `intent` | Count of intents (e.g., SEARCH vs ASK) for business analysis. |
| `cognitive_confidence_score` | Histogram | `provider` | Distribution of model confidence in its predictions. |

---

## API Reference

::: nala.athomic.ai.cognitive.base.CognitiveBaseService

::: nala.athomic.ai.cognitive.factory.CognitiveFactory

::: nala.athomic.ai.schemas.cognitive.IntentClassification

::: nala.athomic.ai.schemas.cognitive.UserIntent