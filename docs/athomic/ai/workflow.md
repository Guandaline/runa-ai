# Workflow Orchestration Engine

## Overview

The **Workflow Orchestration Engine** (`nala.athomic.ai.workflow`) is the backbone for executing complex, non-linear AI logic.
Unlike simple sequential chains, this module enables the creation of **Stateful Graphs** capable of cyclic execution (loops), conditional branching, and self-correction.

It implements the **Dependency Inversion Principle**, strictly separating the *definition* of the workflow (the "What") from the *execution engine* (the "How"). This allows the platform to switch between lightweight in-memory execution and robust, fault-tolerant engines like **LangGraph** without changing business logic.

### Key Features

-   **Cyclic Graphs**: Native support for loops (e.g., "Think -> Act -> Observe -> Think"), essential for autonomous agents.
-   **Engine Agnostic**: Switch providers (`memory`, `langgraph`) via configuration.
-   **Universal Definition**: A standardized `WorkflowDefinition` API that works across all providers.
-   **Service Integration**: Inherits full observability (Metrics, Tracing, Logs) from `BaseService`.
-   **Safety Limits**: Enforces `max_execution_steps` to prevent infinite recursion loops in autonomous agents.

---

## Architecture

The module is built on a **Provider-Based Architecture**:

1.  **Definition Layer**:
    * `WorkflowDefinition`: A generic blueprint container. Developers use this to add **Steps** (Nodes) and **Routes** (Edges).
    * It contains no execution logic, only structure.

2.  **Factory Layer**:
    * `WorkflowEngineFactory`: Reads `settings.toml` and instantiates the correct provider.

3.  **Execution Layer (Providers)**:
    * **`InMemoryWorkflowEngine`**: A pure Python implementation. Fast and lightweight, ideal for unit tests and simple linear flows.
    * **`LangGraphWorkflowEngine`**: An adapter for the **LangGraph** library. Provides enterprise-grade features like checkpointing, thread management, and human-in-the-loop capabilities.

---

## Usage Example

### Defining and Running a Workflow

```python
from typing import Dict, Any
from nala.athomic.ai.workflow import WorkflowDefinition, WorkflowEngineFactory

# 1. Define Step Logic (Nodes)
async def step_research(state: Dict[str, Any]) -> Dict[str, Any]:
    print("Researching...")
    return {"data": "Results found"}

async def step_summarize(state: Dict[str, Any]) -> Dict[str, Any]:
    print("Summarizing...")
    return {"summary": "Short summary"}

# 2. Build the Graph Blueprint
definition = WorkflowDefinition()
definition.add_step("research", step_research)
definition.add_step("summarize", step_summarize)

definition.set_entry_point("research")
definition.add_route("research", "summarize")

async def run_pipeline():
    # 3. Create Engine (Provider determined by settings)
    engine = WorkflowEngineFactory.create_default()
    await engine.connect()

    # 4. Compile & Run
    engine.compile(definition)
    
    result = await engine.run(input_data={"topic": "AI"})
    print(result)
```

### Conditional Branching

```python
def route_logic(state: Dict[str, Any]) -> str:
    return "human_review" if state["confidence"] < 0.5 else "publish"

definition.add_conditional_route(
    source="generate_content",
    condition_fn=route_logic,
    destinations={
        "human_review": "wait_for_approval_node",
        "publish": "publish_node"
    }
)
```

---

## Configuration

The workflow engine is configured under `[ai.workflow]` in `settings.toml`.

```toml
[default.ai.workflow]
enabled = true

# The backend engine to use.
# Options: "memory", "langgraph"
default_provider = "langgraph"

# Safety limit to prevent infinite loops in cyclic graphs.
max_execution_steps = 50

# Enables verbose logging of graph transitions.
debug_mode = true
```

---

## Observability

The engine automatically exports metrics to Prometheus:

| Metric Name | Type | Labels | Description |
| :--- | :--- | :--- | :--- |
| `workflow_executions_total` | Counter | `workflow_name`, `status` | Total number of workflows executed. |
| `workflow_execution_duration_seconds` | Histogram | `workflow_name`, `status` | Total execution time. |
| `workflow_step_duration_seconds` | Histogram | `workflow_name`, `step_name` | Duration of individual steps (nodes). |
| `workflow_steps_count` | Histogram | `workflow_name` | Number of steps taken per execution (useful to detect loops). |

---

## API Reference

::: nala.athomic.ai.workflow.definition.structure.WorkflowDefinition

::: nala.athomic.ai.workflow.protocol.WorkflowEngineProtocol

::: nala.athomic.ai.workflow.factory.WorkflowEngineFactory

::: nala.athomic.config.schemas.ai.workflow.workflow_settings.WorkflowSettings