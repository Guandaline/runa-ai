from nala.athomic.base.exceptions import AthomicError


class AIError(AthomicError):
    """
    Base class for all AI-related exceptions.

    All errors raised within the nala.athomic.ai package should
    inherit from this class to allow granular error handling by
    higher-level components.
    """

    pass
