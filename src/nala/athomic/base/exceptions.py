# src/nala/athomic/exceptions.py
"""
Common exceptions for the Nala Athomic layer.
"""


class AthomicError(Exception):
    """Base class for exceptions raised by Athomic components."""

    pass


class ModuleLoadError(AthomicError):
    """Raised when a Python module cannot be loaded dynamically from a file path."""

    pass
