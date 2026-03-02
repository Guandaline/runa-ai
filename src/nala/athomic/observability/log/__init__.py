# nala/athomic/safelogger/__init__.py

from .filters import default_patterns as patterns
from .filters.sensitive_data_filter import SensitiveDataFilter
from .setup import Logger, get_logger

__all__ = ["get_logger", "SensitiveDataFilter", "patterns", "Logger"]
