# AI Agents

## Overview

The AI Agents module provides a robust, configuration-driven framework for building autonomous agents capable of reasoning and tool execution.
It implements the **ReAct (Reasoning + Acting)** pattern, allowing Large Language Models to interact with external environments, execute tools, and observe results to solve complex, multi-step problems.

### Key Features

-   **ReAct Loop**: Orchestrates the "Think -> Act -> Observe" cycle automatically.
-   **Profile-Based Configuration**: Define agent behaviors, system prompts, and toolsets entirely in `settings.toml` without changing code.
-   **Tool Abstraction**: Decouples the agent from specific tool implementations using a robust `Executor` strategy.
-   **Resilience**: Handles tool execution errors gracefully, feeding errors back to the LLM for self-correction.
-   **Observability**: Full tracing of the reasoning chain (thoughts, actions, observations).
-   **Code Execution Capability**: Native integration with the [Sandbox](./sandbox.md) module via the `CodeInterpreterTool`, allowing agents to securely write and execute Python code to solve mathematical or logical problems.

---

## How It Works

1.  **Initialization**: The `AgentFactory` reads a specific "Agent Profile" from configuration. It resolves the required LLM connection via the `LLMManager` and prepares the `ToolExecutor`.
2.  **Execution Loop (`AgentService.run`)**:
    * **Perceive (Optional)**: The agent can use the `CognitiveService` to pre-classify user input before submitting it to the ReAct loop, allowing shortcuts for simple responses (Chat) or direct RAG.
    * **Think**: The agent sends the conversation history (plus system prompt) to the LLM.
    * **Decide**: The LLM returns either a final answer or a `ToolCall`.
    * **Act**: If a tool is called, the `SyncToolExecutor` executes it safely.
    * **Observe**: The tool's output (result or error) is added to the history as a `TOOL` role message.
    * **Repeat**: The loop continues until the agent provides a final answer or the `max_iterations` limit is reached.

---

## Usage Example

```python
from nala.athomic.ai.agents.factory import AgentFactory

async def run_math_task():
    # 1. Create the agent defined in 'math_agent' profile
    agent = AgentFactory.create(profile_name="math_agent")

    # 2. Run the task
    # The agent will automatically call the 'calculator' tool if needed
    response = await agent.run("What is the square root of 144 multiplied by 5?")
    
    print(response) 
    # Output: "The result is 60."
```

---

## Configuration

Agents are configured under `[ai.agents]` in `settings.toml`. You define reusable **Profiles**.

```toml
[default.ai.agents]
enabled = true
default_profile = "default_assistant"

  # --- Profile: Math Agent ---
  [default.ai.agents.profiles.connections.math_agent]
  name = "math_agent"
  description = "An agent capable of performing calculations."
  system_prompt = "You are a helpful assistant. Use tools for math."
  
  # References a connection defined in [ai.connections]
  connection_name = "openai_gpt4"
  
  # Constraints
  max_iterations = 10
  max_execution_time_seconds = 60
  
  # Allowed Tools (must be registered in ToolRegistry)
  tools = ["calculator_tool", "unit_converter"]
```

---

## API Reference

::: nala.athomic.ai.agents.service.AgentService

::: nala.athomic.ai.agents.factory.AgentFactory

::: nala.athomic.ai.agents.executors.base.BaseToolExecutor

::: nala.athomic.config.schemas.ai.agents.AgentProfileSettings