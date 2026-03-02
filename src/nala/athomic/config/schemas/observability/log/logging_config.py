# src/nala/athomic/config/schemas/observability/log/logging_config.py
import logging
import re
from typing import Any, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

# Type alias for the flexible structure of a sensitive pattern configuration item.
SensitivePatternItemInput = Union[Dict[str, Any], Tuple[Any, Any], List[Any]]


class LoggingSettings(BaseModel):
    """Defines the configuration for the application's logging system.

    This model configures the `Loguru`-based logger, controlling aspects like
    log level, output format, file rotation, and sensitive data masking.

    Attributes:
        level (str): The minimum log level to be processed.
        format (str): The Loguru format string for log records.
        log_to_file (bool): Toggles logging to a file instead of stderr.
        log_file_path (str): The path for the log file.
        rotation (str): The rotation policy for the log file (e.g., "500 MB").
        retention (str): The retention policy for log files (e.g., "10 days").
        compression (Optional[str]): The compression format for rotated logs.
        enqueue (bool): If True, logs are processed in a separate thread.
        backtrace (bool): If True, full stack traces are included for exceptions.
        diagnose (bool): If True, adds extended diagnostic information to exceptions.
        serialize (bool): If True, log records are output as JSON.
        masking_replacement (str): The placeholder string for redacted data.
        sensitive_patterns (List[SensitivePatternItemInput]): A list of patterns
            for the sensitive data filter.
        third_party_log_levels (Dict[str, str]): Overrides log levels for
            third-party libraries.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    level: str = Field(
        default="INFO", alias="LEVEL", description="The minimum log level to process."
    )
    format: str = Field(
        default="{time} {level} {message}",
        alias="FORMAT",
        description="The Loguru format string for log records.",
    )
    log_to_file: bool = Field(
        default=False,
        alias="LOG_TO_FILE",
        description="If True, logs are written to a file instead of stderr.",
    )
    log_file_path: str = Field(
        default=".logs/app.log",
        alias="LOG_FILE_PATH",
        description="The path to the log file if `log_to_file` is True.",
    )
    rotation: str = Field(
        default="500 MB",
        alias="ROTATION",
        description="The rotation policy for log files (e.g., '500 MB', '1 day').",
    )
    retention: str = Field(
        default="10 days",
        alias="RETENTION",
        description="The retention policy for old log files (e.g., '10 days', '1 month').",
    )
    compression: Optional[str] = Field(
        default="zip",
        alias="COMPRESSION",
        description="The compression format for rotated log files (e.g., 'zip', 'gz').",
    )
    enqueue: bool = Field(
        default=True,
        alias="ENQUEUE",
        description="If True, puts log messages into a queue for non-blocking, asynchronous processing.",
    )
    backtrace: bool = Field(
        default=True,
        alias="BACKTRACE",
        description="If True, exception traces are extended upward beyond the catch point.",
    )
    diagnose: bool = Field(
        default=True,
        alias="DIAGNOSE",
        description="If True, adds extended diagnostic information to exception traces.",
    )
    serialize: bool = Field(
        default=False,
        alias="SERIALIZE",
        description="If True, log records are formatted as JSON strings.",
    )
    masking_replacement: str = Field(
        default="***REDACTED***",
        alias="MASKING_REDACTED",
        description="The default placeholder string used to replace sensitive data.",
    )
    sensitive_patterns: List[SensitivePatternItemInput] = Field(
        default_factory=list,
        alias="SENSITIVE_PATTERNS",
        description="A list of custom patterns for the sensitive data filter.",
    )
    third_party_log_levels: Dict[str, str] = Field(
        default_factory=dict,
        alias="THIRD_PARTY_LOG_LEVELS",
        description="A dictionary to override the log levels for specific third-party libraries (e.g., {'httpx': 'WARNING'}).",
    )

    @field_validator("level")
    @classmethod
    def check_log_level(cls, v: str) -> str:
        """Validates that the provided log level string is a valid level."""
        try:
            logging._checkLevel(v.upper())
            return v.upper()
        except (ValueError, TypeError) as e:
            valid_levels = list(logging.getLevelNamesMapping().keys())
            raise ValueError(
                f"Invalid log level '{v}'. Must be one of {valid_levels}"
            ) from e

    @field_validator("third_party_log_levels")
    @classmethod
    def check_third_party_levels(cls, v: Dict[str, str]) -> Dict[str, str]:
        """Validates that all log levels in the third-party dictionary are valid."""
        if not isinstance(v, dict):
            raise TypeError("third_party_log_levels must be a dictionary")
        validated_dict = {}
        valid_levels = list(logging.getLevelNamesMapping().keys())
        for lib_name, level_str in v.items():
            if not isinstance(lib_name, str) or not lib_name:
                raise ValueError(
                    "Library name in third_party_log_levels must be a non-empty string"
                )
            if not isinstance(level_str, str):
                raise ValueError(
                    f"Invalid log level type for library '{lib_name}': Must be a string"
                )
            try:
                logging._checkLevel(level_str.upper())
                validated_dict[lib_name] = level_str.upper()
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Invalid log level '{level_str}' for library '{lib_name}'. Must be one of {valid_levels}"
                ) from e
        return validated_dict

    @field_validator("sensitive_patterns", mode="before")
    @classmethod
    def check_sensitive_patterns_structure(cls, v: Any) -> Any:
        """Ensures that each item in `sensitive_patterns` has a valid structure."""
        if not isinstance(v, list):
            raise TypeError("sensitive_patterns must be a list")

        for idx, item in enumerate(v):
            cls._validate_pattern_item(item, idx)

        return v

    @staticmethod
    def _validate_pattern_item(item: Any, idx: int) -> None:
        """Helper method to validate a single pattern item."""
        pattern_source = f"sensitive_patterns item index {idx}"
        regex, replacement = LoggingSettings._extract_regex_and_replacement(
            item, pattern_source
        )
        LoggingSettings._validate_regex(regex, pattern_source)
        LoggingSettings._validate_replacement(replacement, pattern_source)

    @staticmethod
    def _extract_regex_and_replacement(
        item: Any, pattern_source: str
    ) -> Tuple[Any, Any]:
        """Extracts and validates the regex and replacement from the item."""
        if isinstance(item, dict):
            if "regex" not in item or "replacement" not in item:
                raise ValueError(
                    f"Invalid {pattern_source}: Dictionary must have 'regex' and 'replacement' keys."
                )
            return item["regex"], item["replacement"]
        elif isinstance(item, (list, tuple)) and len(item) == 2:
            return item
        else:
            raise ValueError(
                f"Invalid {pattern_source}: Item must be a dictionary {{'regex': ..., 'replacement': ...}} "
                f"or a tuple/list (regex, replacement)."
            )

    @staticmethod
    def _validate_regex(regex: Any, pattern_source: str) -> None:
        """Validates the regex part of the pattern item."""
        if not isinstance(regex, str):
            raise ValueError(f"Invalid {pattern_source}: 'regex' must be a string.")
        try:
            re.compile(regex)
        except re.error as e:
            raise ValueError(f"Invalid {pattern_source}: Invalid regex '{regex}' - {e}")

    @staticmethod
    def _validate_replacement(replacement: Any, pattern_source: str) -> None:
        """Validates the replacement part of the pattern item."""
        if not isinstance(replacement, str) and not callable(replacement):
            raise ValueError(
                f"Invalid {pattern_source}: 'replacement' must be a string or a callable function, "
                f"got {type(replacement).__name__}."
            )
