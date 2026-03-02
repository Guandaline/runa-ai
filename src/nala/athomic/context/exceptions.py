# src/nala/athomic/context/exceptions.py
from nala.athomic.base.exceptions import AthomicError


class ContextKeyResolutionError(AthomicError):
    """
    Raised when a contextual key resolver fails to extract a required business key.
    """

    pass
