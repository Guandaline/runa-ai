# src/nala/athomic/config/schemas/resilience/adaptive_throttling_config.py

from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdaptiveThrottlingSettings(BaseModel):
    """Defines the configuration for the Adaptive Throttling resilience mechanism.

    This model configures the system that dynamically adjusts rate limits based on
    real-time system health metrics (e.g., latency, error rates) to prevent
    cascading failures. It configures three main components: a State Store for
    dynamic limits, a Metrics Fetcher for health data, and a Decision Algorithm
    for adjusting the limits.

    Attributes:
        enabled (bool): A master switch for the adaptive throttling engine.
        state_store_backend (Literal["redis", "memory"]): The backend for storing
            dynamic rate limits.
        state_store_uri (Optional[str]): Connection URI for the state store if
            it's network-based (e.g., Redis).
        state_store_key_prefix (str): A prefix for all keys in the state store.
        state_store_ttl_seconds (int): The TTL for dynamically set limits.
        metrics_fetcher_type (Literal["prometheus", "dummy"]): The source for
            health metrics.
        metrics_fetcher_url (Optional[str]): The URL for the metrics source.
        prometheus_queries (Dict[str, str]): A map of metric names to PromQL queries.
        decision_algorithm (Literal["threshold"]): The algorithm for adjusting limits.
        algorithm_params (Dict[str, Any]): Parameters for the decision algorithm,
            such as thresholds.
        check_interval_seconds (int): The interval for the check-and-adjust cycle.
        policies_to_adapt (Optional[List[str]]): A list of specific rate limit
            policies to be adapted.
        min_limit_factor (float): The minimum a limit can be reduced to, as a
            fraction of its static configuration.
        max_limit_factor (float): The maximum a limit can be increased to, as a
            fraction of its static configuration.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=False,
        alias="ADAPTIVE_THROTTLING_ENABLED",
        description="A master switch to enable or disable the adaptive throttling engine.",
    )

    state_store_backend: Literal["redis", "memory"] = Field(
        default="memory",
        description="The backend for storing dynamic rate limits. 'memory' is for single-instance, non-persistent state.",
    )
    state_store_uri: Optional[str] = Field(
        default=None,
        description="The connection URI for the state store, required if the backend is 'redis'.",
    )
    state_store_key_prefix: str = Field(
        default="nala:adaptive_limit",
        description="The key prefix used for storing all adaptive limit data in the state store.",
    )
    state_store_ttl_seconds: int = Field(
        default=300,
        description="The Time-To-Live in seconds for a dynamically set limit. After the TTL expires, the system reverts to the statically configured limit.",
    )

    metrics_fetcher_type: Literal["prometheus", "dummy"] = Field(
        default="dummy",
        description="The type of metrics source to use for decision-making (e.g., 'prometheus' or 'dummy' for testing).",
    )
    metrics_fetcher_url: Optional[str] = Field(
        default=None,
        description="The URL of the metrics source, required for backends like 'prometheus'.",
    )
    prometheus_queries: Dict[str, str] = Field(
        default_factory=dict,
        description="A dictionary mapping internal metric names to the PromQL queries used to fetch them.",
    )

    decision_algorithm: Literal["threshold"] = Field(
        default="threshold",
        description="The name of the algorithm used to calculate new rate limits based on the fetched metrics.",
    )
    algorithm_params: Dict[str, Any] = Field(
        default_factory=dict,
        description="Parameters to configure the selected decision algorithm (e.g., latency or error rate thresholds).",
    )
    check_interval_seconds: int = Field(
        default=30,
        description="The interval in seconds at which the engine runs the check-and-adjust cycle.",
    )
    policies_to_adapt: Optional[List[str]] = Field(
        default=None,
        description="A list of specific rate limit policy names to be dynamically adapted. If `None`, only the 'default' policy is adapted.",
    )
    min_limit_factor: float = Field(
        default=0.1,
        description="The minimum allowed value for a dynamic limit, expressed as a fraction of the statically configured limit (e.g., 0.1 for 10%).",
    )
    max_limit_factor: float = Field(
        default=1.0,
        description="The maximum allowed value for a dynamic limit, expressed as a fraction of the statically configured limit (e.g., 1.0 means no increase is allowed).",
    )

    @model_validator(mode="after")
    def check_dependencies(self) -> "AdaptiveThrottlingSettings":
        """A Pydantic validator to ensure dependencies for selected backends are configured.

        This method checks that if a backend like 'redis' or 'prometheus' is
        selected, its corresponding URI/URL is also provided in the configuration.

        Returns:
            AdaptiveThrottlingSettings: The validated settings instance.

        Raises:
            ValueError: If a required dependency is missing.
        """
        if self.state_store_backend == "redis" and not self.state_store_uri:
            raise ValueError(
                "'state_store_uri' is required when 'state_store_backend' is 'redis'"
            )

        if self.metrics_fetcher_type == "prometheus" and not self.metrics_fetcher_url:
            raise ValueError(
                "'metrics_fetcher_url' is required when 'metrics_fetcher_type' is 'prometheus'"
            )

        return self
