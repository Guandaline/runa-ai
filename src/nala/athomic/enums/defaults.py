# src/nala/athomic/enums/defaults.py
"""Defines standardized enumeration for default configuration names."""

from enum import Enum


class Defaults(str, Enum):
    """
    Defines standardized string constants for default names used in configurations,
    such as default database connection names.
    """

    DEFAULT_MONGO_CONNECTION = "default_mongo"
    DEFAULT_REDIS_CONNECTION = "default_redis"
    DEFAULT_CONSUL_CONNECTION = "default_consul"
    DEFAULT_NEO4J_CONNECTION = "default_neo4j"

    # Messaging
    DEFAULT_MESSAGING_CONNECTION = "default_messaging"
    DEFAULT_LINEAGE_PRODUCER = "default_lineage_producer"
    DEFAULT_MESSAGING_UTILITY_QUEUE = "messaging_utility_queue"

    # Event Sourcing
    DEFAULT_SNAPSHOT_FREQUENCY = 50
    DEFAULT_EVENT_STORE = "default_event_store"
    DEFAULT_SNAPSHOT_STORE = "default_snapshot_store"
