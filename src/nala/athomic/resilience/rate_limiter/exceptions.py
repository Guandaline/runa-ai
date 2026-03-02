class RateLimitExceeded(Exception):
    def __init__(self, key: str, limit: str):
        super().__init__(f"Rate limit exceeded for key '{key}' with limit '{limit}'")
        self.key = key
        self.limit = limit
