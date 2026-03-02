from pydantic import BaseModel, ConfigDict, Field, model_validator


class LeasingSettings(BaseModel):
    """Defines the configuration for the distributed leasing mechanism.

    This model configures the distributed leasing system, which is used to
    ensure that only one process in a distributed environment holds the exclusive
    right to perform a task on a specific resource at a time.

    Attributes:
        enabled (bool): A master switch for the leasing system.
        kv_store_connection_name (str): The name of the KVStore connection
            used for managing lease state.
        duration_seconds (int): The duration for which a lease is held
            before it expires.
        renewal_interval_seconds (int): The interval at which an active lease
            is renewed.
        default_acquire_timeout_seconds (int): The default time to wait to
            acquire a lease.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to globally enable or disable the leasing system.",
    )

    kv_store_connection_name: str = Field(
        default="default_redis",
        alias="KV_STORE_CONNECTION_NAME",
        description="The name of the KVStore connection (from `database.kvstore`) to be used for storing and managing lease state.",
    )

    duration_seconds: int = Field(
        default=30,
        gt=0,
        description="The duration in seconds for which a lease is held before it expires if not renewed.",
    )

    renewal_interval_seconds: int = Field(
        default=10,
        gt=0,
        description="The interval in seconds at which an active lease is automatically renewed by its holder.",
    )

    default_acquire_timeout_seconds: int = Field(
        default=5,
        gt=0,
        description="The default time in seconds a process will wait to acquire a lease before timing out.",
    )

    @model_validator(mode="after")
    def check_renewal_is_less_than_duration(self) -> "LeasingSettings":
        """A Pydantic validator to ensure the renewal interval is shorter than the lease duration.

        This check is crucial to prevent a scenario where a lease would always expire
        before its holder has a chance to renew it.

        Returns:
            LeasingSettings: The validated settings instance.

        Raises:
            ValueError: If `renewal_interval_seconds` is greater than or equal to
                `duration_seconds`.
        """
        if self.renewal_interval_seconds >= self.duration_seconds:
            raise ValueError(
                "renewal_interval_seconds must be less than lease_duration_seconds."
            )
        return self
