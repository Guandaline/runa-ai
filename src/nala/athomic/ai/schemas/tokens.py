from pydantic import BaseModel, Field


class TokenBudget(BaseModel):
    """
    Represents the calculated token budget/usage for a specific transaction.
    """

    model_limit: int = Field(
        ...,
        description="The physical hard limit of the model's context window (Capability).",
    )
    effective_limit: int = Field(
        ..., description="The enforced limit after applying policies (Business Rule)."
    )
    system_prompt_tokens: int = Field(
        ..., description="Tokens consumed by system instructions."
    )
    input_tokens: int = Field(..., description="Tokens consumed by user query/input.")
    reserved_output_tokens: int = Field(
        ..., description="Tokens reserved for the model's response."
    )
    available_context_tokens: int = Field(
        ..., description="Remaining tokens available for RAG/Context injection."
    )
    utilization_ratio: float = Field(
        ..., description="Percentage of the effective limit utilized."
    )
