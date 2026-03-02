# AI Quality Assurance & Evaluation

## Overview

The **Nala QA Harness** (`nala.athomic.ai.qa`) is a specialized module designed to evaluate non-deterministic AI systems (like RAG pipelines and Agents). Unlike traditional unit tests that rely on exact equality assertions, this module uses a flexible **Strategy Pattern** to assess quality dimensions such as Faithfulness, Answer Relevancy, and Context Recall.

### Key Features

-   **Model Agnostic**: Can evaluate any system (RAG, Chatbot, Classifier) via the `SystemUnderAssessmentProtocol`.
-   **Pluggable Metrics**: Swap between fast deterministic checks (e.g., keyword match) and deep semantic evaluation (e.g., LLM-as-a-Judge) without changing test code.
-   **Production Observability**: Automatically exports quality scores and pass rates to Prometheus/Grafana to track model drift over time.
-   **Standardized Reporting**: Produces a uniform `QualityEvaluationResult` regardless of the underlying system.

---

## Architecture

The QA module is built upon three core pillars:



1.  **System Under Assessment (SUT)**: The AI component being tested. We use the **Adapter Pattern** (e.g., `RAGAdapter`) to wrap different systems into a uniform protocol.
2.  **Metric Strategies**: Logic that calculates a score (0.0 to 1.0) for a given interaction.
    * **Deterministic**: `ExactMatch`, `KeywordInclusion`, `ContextHit`.
    * **Semantic**: `Faithfulness`, `AnswerRelevancy` (via `ai.evaluation` module).
3.  **Orchestration Service**: The `QAService` manages the execution flow: `Load Case -> Run System -> Calculate Metrics -> Record Telemetry`.

---

## Usage Example

### Running a RAG Evaluation

This example demonstrates how to evaluate a RAG pipeline against a "Golden Dataset" case using the `RAGAdapter`.

```python
import asyncio
from nala.athomic.ai.qa.service import QAService
from nala.athomic.ai.qa.adapters.rag_adapter import RAGAdapter
from nala.athomic.ai.evaluation.strategies.basic import KeywordInclusionStrategy, ContextHitStrategy
from nala.athomic.ai.schemas.qa import QualityCase
from nala.athomic.config.schemas.ai.qa import QASettings

# 1. Define the Test Case (Ground Truth)
case = QualityCase(
    id="TC-RAG-001",
    input_data="What is the capital of France?",
    expected_output="Paris",
    expected_context_ids=["doc_france_wiki_01"],
    metadata={"difficulty": "easy", "domain": "geography"}
)

async def run_evaluation(rag_service_instance):
    # 2. Configuration
    settings = QASettings(enabled=True, model_alias="gpt-4-turbo")

    # 3. Define Strategies
    strategies = [
        KeywordInclusionStrategy(threshold=0.8), # Must contain "Paris"
        ContextHitStrategy(threshold=1.0)        # Must retrieve specific doc
    ]

    # 4. Initialize Service with Adapter
    adapter = RAGAdapter(rag_service=rag_service_instance)
    
    service = QAService(
        settings=settings,
        system_adapter=adapter,
        metric_strategies=strategies,
        service_name="nightly_rag_eval"
    )
    await service.connect()

    # 5. Evaluate
    result = await service.evaluate_case(case)

    # 6. Inspect Results
    print(f"Overall Pass: {result.all_passed}")
    print(f"Metrics: {result.metrics}")

# ... execute run_evaluation() in your event loop
```

---

## Configuration

The QA Harness is configured under `[ai.qa]` in `settings.toml`.

```toml
[default.ai.qa]
enabled = true

# Global pass/fail threshold for suites
default_threshold = 0.7

# Optional: Path to golden dataset for regression testing
default_dataset_path = "./tests/resources/datasets/golden_qa.jsonl"

# Output directory for reports
output_path = "./artifacts/qa"
```

---

## Metric Strategies

### Deterministic (Basic)

These are fast, free, and require no LLM calls. Ideal for smoke tests and CI/CD pipelines.

| Strategy | Description |
| :--- | :--- |
| `ExactMatchStrategy` | Checks if the output matches the expected string exactly (supports case-insensitivity). |
| `KeywordInclusionStrategy` | Verifies that specific keywords from `expected_output` are present in the response. |
| `ContextHitStrategy` | (RAG only) Checks if the `expected_context_ids` were found in the retrieved documents. |

### Semantic (LLM-based)

These require the `ai.evaluation` module and use an LLM-as-a-Judge. Ideal for nightly evaluation and quality monitoring.

| Strategy | Description |
| :--- | :--- |
| `Faithfulness` | Checks if the answer is grounded in the retrieved context (Hallucination detection). |
| `AnswerRelevancy` | Checks if the answer actually addresses the user query. |
| `ContextRecall` | Checks if the retrieved context contains the information needed to answer the query. |

---

## Observability

The QA Service automatically exports metrics to Prometheus.

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `rag_quality_last_score` | Gauge | `dataset`, `metric_name`, `model_used` | The most recent score for a specific metric. |
| `rag_quality_score_distribution` | Histogram | `dataset`, `metric_name`, `model_used` | Historical distribution of scores (detects drift). |
| `rag_quality_failures_total` | Counter | `dataset`, `metric_name`, `model_used` | Total number of test cases that failed the threshold. |
| `rag_evaluation_duration_seconds` | Histogram | `metric_name` | Latency overhead of the evaluation logic itself. |

---

## API Reference

::: nala.athomic.ai.qa.service.QAService

::: nala.athomic.ai.qa.adapters.rag_adapter.RAGAdapter

::: nala.athomic.ai.schemas.qa.QualityCase

::: nala.athomic.ai.schemas.qa.QualityEvaluationResult