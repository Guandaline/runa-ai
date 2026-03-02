from prometheus_client import Gauge

# A gauge for each external dependency we want to monitor.
redis_up = Gauge(
    "redis_up", "Indicates if the connection to Redis is operational (1 = up, 0 = down)"
)
kafka_up = Gauge(
    "kafka_up", "Indicates if the connection to Kafka is operational (1 = up, 0 = down)"
)
mongodb_up = Gauge(
    "mongodb_up",
    "Indicates if the connection to MongoDB is operational (1 = up, 0 = down)",
)
