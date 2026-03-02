# src/nala/athomic/enums/languages.py
"""Defines standardized enumeration for supported programming languages."""

from enum import Enum


class PlatformLanguage(str, Enum):
    """
    Standardized list of programming languages supported by the Nala Platform.

    This enum acts as the source of truth for:
    - nala.athomic.execution (selecting container images/runtimes)
    - nala.athomic.ai.sandbox (validating agent requests)
    - nala.athomic.settings (configuration validation)
    """

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    BASH = "bash"
    GO = "go"
