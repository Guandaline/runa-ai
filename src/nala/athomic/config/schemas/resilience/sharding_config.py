# nala/athomic/config/schemas/resilience/sharding_config.py
from typing import Dict

from pydantic import BaseModel, ConfigDict, Field


class ShardingPolicySettings(BaseModel):
    """Defines the configuration for a single sharding group policy.

    This model defines a group of workers that will share a workload. The
    `group_name` is the key used in the service discovery system to identify
    all members of this group.

    Attributes:
        group_name (str): The service discovery name for the group of workers.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    group_name: str = Field(
        ...,
        description="The name used in the service discovery system (e.g., Consul) for the group of workers that will participate in this sharding policy.",
    )


class ShardingSettings(BaseModel):
    """Defines the main configuration for the distributed workload sharding service.

    This model configures the sharding mechanism, which distributes a workload
    (e.g., a set of tasks or aggregate keys) among a dynamic group of worker
    instances using consistent hashing. It relies on a service discovery
    backend to find active workers for a given policy.

    Attributes:
        enabled (bool): A master switch for the sharding mechanism.
        policies (Dict[str, ShardingPolicySettings]): A dictionary of named
            sharding policies.
    """

    model_config = ConfigDict(extra="ignore", populate_by_name=True)

    enabled: bool = Field(
        default=True,
        description="A master switch to globally enable or disable the sharding mechanism.",
    )

    policies: Dict[str, ShardingPolicySettings] = Field(
        default_factory=dict,
        description="A dictionary of named sharding policies. The key is a logical name (e.g., 'outbox_publishers'), and the value defines the service discovery group.",
    )
