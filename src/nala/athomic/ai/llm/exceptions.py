# src/nala/athomic/ai/llm/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class LLMError(AthomicError):
    """Base exception for all errors originating from the AI/LLM module."""

    pass


class LLMGenerationError(LLMError):
    """Raised when the high-level generation process fails."""

    pass


class ProviderError(LLMError):
    """
    Raised when the underlying provider (Vertex, OpenAI) returns an API error.
    Used for 5xx errors, timeouts, or unreachability.
    """

    pass


class ProviderInitializationError(ProviderError):
    """
    Raised when the LLM provider fails to initialize properly,
    such as due to invalid configuration or missing credentials.
    """

    pass


class AuthenticationError(ProviderError):
    """
    Raised when authentication with the provider fails (401/403).
    Useful to trigger alerts for expired keys or permission issues.
    """

    pass


class RateLimitError(ProviderError):
    """
    Raised when the provider's API rate limit is exceeded (429).
    Note: This is distinct from our internal Governance Rate Limit.
    """

    pass


class ContextWindowExceededError(LLMError):
    """
    Raised when the prompt + completion exceeds the model's maximum context length.
    Triggers for fallback strategies (e.g., summarization, chunking).
    """

    def __init__(self, model: str, token_count: int, limit: int):
        self.model = model
        self.token_count = token_count
        self.limit = limit
        super().__init__(
            f"Context window exceeded for model '{model}'. "
            f"Tokens: {token_count}/{limit}."
        )


class StructuredOutputError(LLMError):
    """
    Raised when the model fails to generate a valid JSON/Structure matching the
    requested Pydantic schema, even after internal retries.
    """

    def __init__(self, schema_name: str, raw_output: str):
        self.schema_name = schema_name
        self.raw_output = raw_output[:500]
        super().__init__(
            f"Failed to parse structured output for schema '{schema_name}'."
        )


class InvalidRequestError(LLMError):
    """
    Raised when the input parameters (temperature, stop_sequences) are invalid
    or rejected by the provider (400 Bad Request).
    """

    pass
