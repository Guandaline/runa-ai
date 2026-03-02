# Agent State Persistence

## Overview

The Agent Persistence module allows AI Agents to save their execution state (conversation history, variables, and current step) to a durable storage backend. This enables:

1.  **Fault Tolerance:** Resuming execution if the process crashes.
2.  **Long-Running Threads:** Pausing an agent and resuming it hours or days later.
3.  **Observability:** Inspecting the intermediate states of an agent's reasoning loop.

---

## Architecture

The system uses a **Provider Pattern** to decouple the agent logic from the storage technology.

* **CheckpointProtocol:** The interface defining `save`, `load`, and `delete` operations.
* **AgentService:** The consumer. It attempts to restore state on startup and saves state after every "Think" (LLM call) and "Act" (Tool execution) cycle.
* **Providers:**
    * `KVCheckpoint`: Optimized for speed using Key-Value stores (Redis, In-Memory). Ideal for short-lived sessions or caching.
    * `DocumentCheckpoint`: Optimized for queryability using Document stores (MongoDB). Ideal for long-term history and auditing.

---

## Configuration

Persistence is configured in `settings.toml` under `[ai.agents.persistence]`.

### Enabling Persistence

```toml
[default.ai.agents.persistence]
enabled = true
strategy = "kv_store"  # Options: "kv_store", "document"
connection_name = "default_redis" # Must match a connection in [database] section
namespace = "agent_sessions"
ttl_seconds = 86400 # 24 hours
```

### Strategy: Key-Value Store (Redis)

Best for high-performance, ephemeral session storage.

```toml
[default.ai.agents.persistence]
strategy = "kv_store"
connection_name = "default_redis" # Defined in [database.kvstore]
```

### Strategy: Document Store (MongoDB)

Best for complex state structures and when you need to query history by fields other than ID.

```toml
[default.ai.agents.persistence]
strategy = "document"
connection_name = "default_mongo" # Defined in [database.documents]
namespace = "agent_checkpoints"   # Acts as the Collection Name
```

---

## Usage

### Creating a Persisted Agent

To enable persistence for a specific agent execution, you must provide a `thread_id` to the `AgentFactory`.

```python
from nala.athomic.ai.agents.factory import AgentFactory

# 1. User starts a chat session (frontend generates a UUID)
session_id = "550e8400-e29b-41d4-a716-446655440000"

# 2. Create the Agent with the thread_id
agent = AgentFactory.create(
    profile_name="support_bot",
    thread_id=session_id
)

# 3. Run the agent
# If 'session_id' exists in DB, history is restored automatically.
# If 'session_id' is new, a new history starts.
response = await agent.run("Hello, I need help with my order.")
```

### Clearing State

To restart a conversation or comply with privacy requests (Right to be Forgotten), you can delete the persistence state.

```python
# (Assuming you have access to the checkpointer instance or via a management service)
await agent.checkpointer.delete(session_id)
```

---

## Internals

### Checkpoint Data Structure

The state is saved as a JSON-compatible dictionary:

```json
{
  "agent_profile": "support_bot",
  "current_step": 2,
  "updated_at": "2023-10-27T10:00:00Z",
  "variables": {
    "user_name": "Alice"
  },
  "history": [
    {
      "role": "system",
      "content": "You are a helpful assistant."
    },
    {
      "role": "user",
      "content": "Check order #123"
    },
    {
      "role": "assistant",
      "content": "Checking database...",
      "metadata": { "tool_calls": [...] }
    },
    {
      "role": "tool",
      "name": "check_order_status",
      "content": "{'status': 'shipped'}"
    }
  ]
}
```

### Error Handling

If the persistence provider fails (e.g., Redis is down):
1.  The error is logged as a warning.
2.  The `AgentService` **continues execution** in volatile mode (in-memory only).
3.  This ensures that infrastructure glitches do not cause the user request to fail immediately, providing graceful degradation.