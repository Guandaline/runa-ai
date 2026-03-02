# src/nala/athomic/observability/log/setup.py
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

from loguru import logger
from loguru._logger import Logger

from nala.athomic.config.schemas.observability.log import LoggingSettings
from nala.athomic.observability.log.filters.sensitive_data_filter import (
    SensitiveDataFilter,
)

#
# Constant for the fallback log format
FALLBACK_LOG_FORMAT = "FALLBACK LOGGER: {level} - {message}"


class LoggingManager:
    """
    Manages the application's logging configuration as a singleton.

    Ensures that logging is configured only once (idempotency), providing a
    centralized, robust, and failure-resilient setup process for Loguru.
    """

    def __init__(self) -> None:
        self._configured = False
        # Define a minimal internal logger for the manager itself before configuration
        self.internal_logger = logger.bind(name="LoggingManager")
        self.internal_logger.remove()
        self.internal_logger.add(sys.stderr, level="INFO")

    def configure(self, settings: Optional[LoggingSettings] = None) -> None:
        """
        Configures the global Loguru logger based on provided settings.

        This method is idempotent and will only run the full setup once. It
        includes crucial mechanisms for handling sensitive data filters and
        critical configuration failures.
        """
        if self._configured:
            self.internal_logger.debug("Logging already configured. Skipping.")
            return

        if not settings:
            self.internal_logger.warning(
                "No logging configuration provided. Using basic stderr logger."
            )
            # Loguru's default setup is usually INFO to stderr, which is acceptable
            self._configured = True
            return

        self.internal_logger.info("Initializing logger configuration...")
        logger.remove()  # Clear all existing handlers from the global logger

        try:
            filter_instance = self._create_filter(settings)
            common_args = self._build_common_args(settings, filter_instance)

            if settings.log_to_file:
                self._add_file_sink(settings, common_args)
            else:
                logger.add(sys.stderr, **common_args)
                self.internal_logger.info("Console (stderr) sink configured.")

            if settings.third_party_log_levels:
                self._configure_third_party_logging(settings.third_party_log_levels)

            self.internal_logger.success("Logger configuration applied successfully.")
            if filter_instance is None:
                self.internal_logger.warning(
                    "SensitiveDataFilter failed to initialize. Sensitive data may not be masked."
                )

        except Exception as e:
            self._setup_fallback_logger(e)

        self._configured = True

    def _create_filter(
        self, settings: LoggingSettings
    ) -> Optional[SensitiveDataFilter]:
        """
        Creates the SensitiveDataFilter instance, responsible for masking
        PII and other sensitive patterns in log messages.
        """
        try:
            return SensitiveDataFilter(
                patterns_config=settings.sensitive_patterns,
                default_masking_replacement=settings.masking_replacement,
            )
        except Exception as e:
            # Logs failure but allows the rest of the configuration to proceed
            self.internal_logger.opt(exception=True).error(
                f"CRITICAL: Failed to initialize SensitiveDataFilter: {e}. Logging will not mask sensitive data."
            )
            return None

    def _build_common_args(
        self, settings: LoggingSettings, filter_instance: Optional[SensitiveDataFilter]
    ) -> Dict[str, Any]:
        """Builds a dictionary of common arguments shared by all Loguru sinks."""
        return {
            "level": settings.level.upper(),
            "format": settings.format,
            "filter": filter_instance,
            "enqueue": settings.enqueue,
            "backtrace": settings.backtrace,
            "diagnose": settings.diagnose,
            "serialize": settings.serialize,
        }

    def _add_file_sink(
        self, settings: LoggingSettings, common_args: Dict[str, Any]
    ) -> None:
        """Adds and configures a file sink with rotation and retention policies."""
        log_path = Path(settings.log_file_path)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        logger.add(
            sink=log_path,
            rotation=settings.rotation,
            retention=settings.retention,
            compression=settings.compression,
            **common_args,
        )
        self.internal_logger.info(f"File sink configured at: {log_path}")

    def _configure_third_party_logging(self, log_levels: Dict[str, str]) -> None:
        """Sets log levels for specified third-party libraries (bridging Loguru and stdlib logging)."""
        self.internal_logger.debug(f"Configuring third-party log levels: {log_levels}")
        for lib, level in log_levels.items():
            try:
                logging.getLogger(lib).setLevel(level.upper())
                self.internal_logger.debug(
                    f"Set log level for '{lib}' to {level.upper()}"
                )
            except (ValueError, TypeError):
                self.internal_logger.warning(
                    f"Invalid log level '{level}' for library '{lib}'."
                )

    def _setup_fallback_logger(self, error: Exception) -> None:
        """
        Sets up a minimal, guaranteed-to-work fallback logger in case the main
        configuration fails due to dependency or configuration errors.
        """
        sys.stderr.write(
            f"CRITICAL LOGGING CONFIGURATION ERROR: {type(error).__name__} - {error}\n"
        )
        logger.remove()
        logger.add(sys.stderr, level="INFO", format=FALLBACK_LOG_FORMAT)
        logger.opt(exception=True).critical(f"Logger setup failed critically: {error}")


# Public functions interacting with the singleton
def configure_logging(log_settings: Optional["LoggingSettings"] = None) -> None:
    """
    Public function to trigger the logging configuration process.
    It retrieves the singleton instance of LoggingManager and calls its configure method.
    """
    manager = LoggingManager()
    manager.configure(settings=log_settings)


def get_logger(name: Optional[str] = None) -> Logger:
    """
    Retrieves a logger instance, binding the component name if provided.
    This is the primary way for application modules to obtain a logger instance.
    """
    if name:
        return logger.bind(name=name)
    return logger
