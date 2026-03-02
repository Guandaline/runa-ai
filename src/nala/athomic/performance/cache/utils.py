import secrets


def apply_jitter(ttl: int, jitter_ratio: float = 0.1) -> int:
    """
    Applies a random jitter to the TTL value to reduce cache stampedes.

    Args:
        ttl (int): Base TTL in seconds.
        jitter_ratio (float): Percentage of jitter range to apply.

    Returns:
        int: TTL value with jitter applied.
    """
    jitter = int(ttl * jitter_ratio)
    return ttl + secrets.choice(range(-jitter, jitter + 1))
