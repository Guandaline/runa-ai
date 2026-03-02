from typing import Any, Callable, Optional, Tuple, Type


class RetryPolicy:
    """
    Define the retry behavior: exceptions, attempts, delays, backoff, jitter, etc.
    """

    def __init__(
        self,
        attempts: int = 3,
        wait_min_seconds: float = 0.01,
        wait_max_seconds: float = 60.0,
        backoff: float = 1.0,
        jitter: Optional[float] = None,
        timeout: Optional[float] = None,
        exceptions: Tuple[Type, ...] = (Exception,),
        retry_on_result: Optional[Callable[[Any], bool]] = None,
        should_retry: Optional[Callable[[BaseException], bool]] = None,
    ):
        if attempts < 1:
            raise ValueError("Attempts must be at least 1")

        self.attempts = attempts
        self.wait_min_seconds = wait_min_seconds
        self.wait_max_seconds = wait_max_seconds
        self.backoff = backoff
        self.jitter = jitter
        self.timeout = timeout
        self.exceptions = exceptions
        self.retry_on_result = retry_on_result
        self.should_retry = should_retry
