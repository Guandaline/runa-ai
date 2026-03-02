# src/nala/athomic/config/schemas/app_settings.py
from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

from .ai import AISettings
from .context.context_config import ContextSettings
from .database.database_config import DatabaseSettings
from .observability.log.logging_config import LoggingSettings
from .observability.observability_config import ObservabilitySettings
from .performance.performance_config import PerformanceSettings
from .resilience.resilience_config import ResilienceSettings
from .server.server_config import ServerSettings
from .usage import UsageSettings


class AppSettings(BaseModel):
    """The root Pydantic model for the entire application's configuration."""

    model_config = ConfigDict(
        extra="ignore",
        validate_assignment=True,
        populate_by_name=True,
        case_sensitive=False,
    )

    enabled: bool = Field(
        default=True,
        alias="ENABLED",
        description="A master switch to enable or disable the Athomic layer.",
    )
    app_name: str = Field(
        ..., alias="APP_NAME", description="The name of the application."
    )
    env: Literal["default", "development", "staging", "production"] = Field(
        default="default",
        alias="ENV",
        description="The current application environment.",
    )
    deployment_mode: Optional[Literal["standalone", "mesh"]] = Field(
        default="standalone",
        alias="DEPLOYMENT_MODE",
        description="Defines the network deployment strategy ('standalone' or 'mesh').",
    )
    timeout: Optional[float] = Field(
        default=30.0,
        alias="TIMEOUT",
        description="Default timeout in seconds for connecting to external services.",
    )

    log_level: str = Field(
        default="INFO", alias="LOG_LEVEL", description="The global logging level."
    )
    tags: List[str] = Field(
        default_factory=list,
        alias="TAGS",
        description="A list of tags for categorization or filtering.",
    )

    server: Optional[ServerSettings] = Field(
        default_factory=ServerSettings,
        alias="SERVER",
        description="Server binding configuration (host and port).",
    )

    ai: Optional[AISettings] = Field(
        default_factory=AISettings,
        alias="AI",
        description="Top-level configuration for the AI Foundation module.",
    )

    logging: Optional[LoggingSettings] = Field(
        default_factory=LoggingSettings,
        alias="LOGGING",
        description="Configuration for the logging system.",
    )

    context: Optional[ContextSettings] = Field(
        default_factory=ContextSettings,
        alias="CONTEXT",
        description="Settings for context management and propagation.",
    )

    performance: Optional[PerformanceSettings] = Field(
        default_factory=PerformanceSettings,
        alias="PERFORMANCE",
        description="Settings related to application performance, such as caching.",
    )

    observability: Optional[ObservabilitySettings] = Field(
        default_factory=ObservabilitySettings,
        alias="OBSERVABILITY",
        description="Configuration for observability tools (Tracing, Metrics).",
    )

    database: Optional[DatabaseSettings] = Field(
        default=None,
        alias="DATABASE",
        description="Settings for all database connections (e.g., Document, KVStore).",
    )

    resilience: Optional[ResilienceSettings] = Field(
        default_factory=ResilienceSettings,
        alias="RESILIENCE",
        description="Settings for all resilience patterns (Retry, Circuit Breaker, etc.).",
    )

    usage: UsageSettings = Field(
        default_factory=UsageSettings,
        alias="USAGE",
        description="Configuration for the usage (consumption tracking) module.",
    )


AppSettings.model_rebuild()
