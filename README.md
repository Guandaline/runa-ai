
# Athomic HR Assistant - Technical Challenge

This project implements an intelligent HR Assistant capable of managing vacation requests, checking balances, and retrieving company policies. The implementation leverages a stable slice of the **Athomic Framework (WIP)**, focusing on scalable infrastructure for AI Agents.

## Architecture Overview

The project's architecture is inherited from the **Athomic** framework, following strict separation of concerns and service-oriented design:

* **`src/nala/athomic` (Core Infra/AI)**: The infrastructure layer. It manages the Agent lifecycle, the ReAct (Reasoning + Acting) loop, LLM orchestration, and state persistence. It includes centralized management of execution context, including tenant, request, and trace identifiers.
* **`src/nala/domain` (Business Logic)**: Contains the domain-specific tools required for this challenge (Vacation, Policy, and Time-Off requests). These tools are decoupled from the AI engine, making them independently testable.
* **`src/nala/api` (Interface Layer)**: The entry point of the application. It exposes the `/chat` endpoint using FastAPI and contains the `HRAssistantService`, which orchestrates the flow between the API request and the HR Agent.

---

## Key Technical Features

### Stateless Agent Orchestration
Unlike traditional implementations that store state within the Agent instance, the Athomic-based Agent is **Stateless**. Conversation history and runtime variables are managed within the local scope of the `run` method. 
* **Benefit**: This allows the `HRAssistantService` to use the Agent as a **Singleton**, handling multiple concurrent requests without state leakage between different users or sessions.

### Runtime Context Injection
To ensure high reliability when using small-scale models (such as **Llama 3.2 1B**), we implemented a safety middleware for argument injection.
* **How it works**: If the LLM fails to extract mandatory parameters (like `employee_id`) from the prompt, the Agent's execution engine automatically injects the validated data from the request context variables before triggering the tool.

### Unified Observability and Tracing
The project implements a cohesive tracing system where identity is managed by the `ContextVarManager`. 
* The `request_id` and `trace_id` are registered as thread-safe and async-safe variables.
* These identifiers are propagated from the API middleware through the HR Service and into the Tool Execution layer.
* This ensures that every log entry and tool action is tied to the original request identifier for distributed tracing.

---

## Tech Stack

* **Base Framework**: Athomic (Internal WIP Framework).
* **API**: FastAPI.
* **LLM Engine**: Ollama / OpenAI Protocol (Optimized for Llama 3.2 1B).
* **Documentation**: Detailed project documentation available via **MkDocs**.
    * **Architecture Decision Records (ADRs)**: Included in the documentation to provide transparency into the framework's design choices and architectural evolution.

---

## Getting Started

The project includes a `Makefile` to simplify setup and execution.

```bash
# 1. Install dependencies and setup environment
make install

# 2. Start infrastructure (Containers/Services)
make up

# 3. Run the application locally
make run
```

### Testing the Chat

You can test the assistant using the following `curl` command:

```bash
curl -X 'POST' [http://0.0.0.0:8000/chat](http://0.0.0.0:8000/chat) 
     -H 'Content-Type: application/json' 
     -d '{
       "employee_id": "emp_01",
       "message": "How many vacation days do I have left?",
       "session_id": "session_abc_123"
     }'
```

Or at: http://0.0.0.0:8000/docs