# src/nala/athomic/ai/cognitive/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class CognitiveError(AthomicError):
    """Base exception for all Cognitive Services related failures."""

    pass


class IntentClassificationError(CognitiveError):
    """Raised when the intent classification process fails (e.g., LLM error, parsing error)."""

    pass


class StrategyNotFoundError(CognitiveError):
    """Raised when a requested cognitive strategy (e.g., 'ml_ensemble') is not registered."""

    pass


class CognitiveConfigurationError(CognitiveError):
    """Raised when the cognitive settings are invalid or incomplete."""

    pass
