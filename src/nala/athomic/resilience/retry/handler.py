# nala/athomic/resilience/retry/handler.py

import asyncio
from typing import Any, Callable, Optional, Type, Union

from tenacity import (
    AsyncRetrying,
    Retrying,
    retry_if_exception,
    retry_if_exception_type,
    retry_if_result,
    stop_after_attempt,
    wait_random_exponential,
)

from nala.athomic.observability.log import Logger, get_logger
from nala.athomic.observability.metrics.usage import (
    retry_attempts_total,
    retry_circuit_breaker_aborts_total,
    retry_failures_total,
)
from nala.athomic.observability.tracing import Tracer, get_tracer

from .exceptions import RetryError
from .policy import RetryPolicy

RetryCallback = Optional[Callable[[int, BaseException], None]]
FailCallback = Optional[Callable[[BaseException], None]]


class RetryHandler:
    """
    Manages the retry logic for synchronous and asynchronous functions based on a defined policy.

    This class encapsulates the retry behavior, using the `tenacity` library,
    and integrates framework features such as exponential backoff, observability
    (logging, tracing, metrics), and circuit breaker integration.
    """

    def __init__(
        self,
        policy: RetryPolicy,
        operation_name: Optional[str] = None,
        on_retry: Optional[RetryCallback] = None,
        on_fail: Optional[FailCallback] = None,
        circuit_breaker_hook: Optional[Callable[[], bool]] = None,
        tracer: Optional[Tracer] = None,
        logger: Optional[Logger] = None,
    ):
        """
        Initializes the RetryHandler.

        Args:
            policy (RetryPolicy): The retry policy defining behavior (attempts, delays, exceptions).
            operation_name (Optional[str]): A descriptive name for the operation, used in logs and metrics.
            on_retry (Optional[RetryCallback]): Hook executed before sleep on each failed retry attempt.
            on_fail (Optional[FailCallback]): Hook executed when all retry attempts fail permanently.
            circuit_breaker_hook (Optional[Callable[[], bool]]): Hook function that returns True if the circuit is open, aborting retries.
            tracer (Optional[Tracer]): OpenTelemetry tracer instance.
            logger (Optional[Logger]): Logger instance for instrumentation.
        """
        self.policy: RetryPolicy = policy or RetryPolicy()
        self.operation_name: Optional[str] = operation_name
        self.on_retry_user_callback: RetryCallback = on_retry
        self.on_fail_user_callback: FailCallback = on_fail
        self._circuit_breaker_hook = circuit_breaker_hook
        self._tracer: Optional[Tracer] = tracer
        self._logger: Logger = logger or get_logger(__name__)

    def _get_tracer(self) -> Tracer:
        """Retrieves the appropriate OpenTelemetry Tracer instance."""
        return self._tracer or get_tracer(__name__)

    def _get_operation_label(self, function_name: str) -> str:
        """Determines the label to use for metrics and logging."""
        return self.operation_name or function_name

    def _before_attempt(self, retry_state):
        """
        Hook executed before each attempt (including the first one) to check the circuit breaker status.
        """
        operation_label = self._get_operation_label(retry_state.fn.__name__)

        if self._circuit_breaker_hook and self._circuit_breaker_hook():
            self._logger.warning(
                f"Circuit breaker open for '{operation_label}'. Aborting retry."
            )
            retry_circuit_breaker_aborts_total.labels(operation=operation_label).inc()
            tracer = self._get_tracer()
            current_span = getattr(tracer, "get_current_span", lambda: None)()

            if current_span:
                current_span.add_event(
                    "retry.circuit_breaker.aborted", {"operation": operation_label}
                )

            raise RetryError("Circuit breaker is open.")

    def _before_sleep(self, retry_state):
        """
        Hook executed before waiting/sleeping between failed attempts.
        It logs the failure reason and updates attempt metrics.
        """
        operation_label = self._get_operation_label(retry_state.fn.__name__)
        if retry_state.outcome.failed:
            log_reason = "exception"
            exc = retry_state.outcome.exception()
            log_message = (
                f"Attempt {retry_state.attempt_number} for '{operation_label}' "
                f"failed due to {type(exc).__name__}. Retrying..."
            )
        else:
            log_reason = "result"
            result = retry_state.outcome.result()
            log_message = (
                f"Attempt {retry_state.attempt_number} for '{operation_label}' "
                f"failed due to invalid result '{str(result)[:50]}'. Retrying..."
            )

        self._logger.bind(
            operation=operation_label,
            attempt=retry_state.attempt_number,
            wait_seconds=retry_state.next_action.sleep,
            reason=log_reason,
        ).warning(log_message)

        retry_attempts_total.labels(operation=operation_label).inc()
        tracer = self._get_tracer()
        current_span = getattr(tracer, "get_current_span", lambda: None)()

        if current_span:
            current_span.add_event(
                "retry.attempt.failed",
                {
                    "operation": operation_label,
                    "retry.reason": log_reason,
                    "retry.attempt_number": retry_state.attempt_number,
                },
            )

        if self.on_retry_user_callback and retry_state.outcome.failed:
            try:
                self.on_retry_user_callback(
                    retry_state.attempt_number, retry_state.outcome.exception()
                )
            except Exception as callback_exc:
                self._logger.bind(
                    operation=operation_label,
                    attempt=retry_state.attempt_number,
                    callback="on_retry",
                ).error(f"Retry callback raised: {repr(callback_exc)}")

    def _build_retry_predicate(self) -> Any:
        """Constructs the combined retry condition based on exceptions and result."""
        predicates = []
        base_exception_predicate = retry_if_exception_type(self.policy.exceptions)
        if self.policy.should_retry:

            def custom_exception_predicate(exc: BaseException) -> bool:
                return base_exception_predicate(exc) and self.policy.should_retry(exc)

            predicates.append(retry_if_exception(custom_exception_predicate))
        else:
            predicates.append(base_exception_predicate)
        if self.policy.retry_on_result:
            predicates.append(retry_if_result(self.policy.retry_on_result))
        if len(predicates) > 1:
            return predicates[0] | predicates[1]
        return predicates[0]

    def _create_retry_engine(
        self, engine_class: Union[Type[Retrying], Type[AsyncRetrying]]
    ):
        """Creates and configures the `tenacity` engine instance."""
        return engine_class(
            stop=stop_after_attempt(self.policy.attempts),
            wait=wait_random_exponential(
                multiplier=self.policy.backoff,
                min=self.policy.wait_min_seconds,
                max=self.policy.wait_max_seconds,
            ),
            retry=self._build_retry_predicate(),
            before=self._before_attempt,
            before_sleep=self._before_sleep,
            reraise=True,
        )

    def _handle_final_failure(self, fn_name: str, exc: Optional[BaseException]) -> None:
        """
        Centralized handling for permanent failures after all attempts.
        It logs the failure, calls the `on_fail` hook, and raises a final `RetryError`.
        """
        operation_label = self._get_operation_label(fn_name)
        self._logger.bind(
            operation=operation_label, attempts=self.policy.attempts
        ).error(
            f"Operation '{operation_label}' failed permanently after {self.policy.attempts} attempts."
        )

        retry_failures_total.labels(operation=operation_label).inc()

        final_exception = exc or RetryError(
            f"Operation '{operation_label}' failed due to an invalid result after all retries."
        )
        if self.on_fail_user_callback:
            try:
                self.on_fail_user_callback(final_exception)
            except Exception as callback_exc:
                self._logger.bind(operation=operation_label, callback="on_fail").error(
                    f"Fail callback raised: {repr(callback_exc)}"
                )
        raise RetryError(
            f"Operation '{operation_label}' failed after all retries."
        ) from final_exception

    def run(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Executes a synchronous function with the configured retry policy.
        """
        retryer = self._create_retry_engine(Retrying)
        try:
            result = retryer(fn, *args, **kwargs)
            if self.policy.retry_on_result and self.policy.retry_on_result(result):
                raise RetryError(
                    f"Operation '{self._get_operation_label(fn.__name__)}' finished with an invalid result after all attempts: {result}"
                )
            return result
        except (KeyboardInterrupt, SystemExit):
            raise
        except RetryError:
            raise
        except Exception as e:
            # Only handle exceptions listed in the policy; unlisted exceptions propagate immediately
            if not isinstance(e, self.policy.exceptions):
                raise
            self._handle_final_failure(fn.__name__, e)

    async def arun(self, fn: Callable, *args, **kwargs) -> Any:
        """
        Executes an asynchronous function with the configured retry policy.
        """
        retryer = self._create_retry_engine(AsyncRetrying)
        try:
            if self.policy.timeout:
                result = await asyncio.wait_for(
                    retryer(fn, *args, **kwargs), timeout=self.policy.timeout
                )
            else:
                result = await retryer(fn, *args, **kwargs)
            if self.policy.retry_on_result and self.policy.retry_on_result(result):
                raise RetryError(
                    f"Operation '{self._get_operation_label(fn.__name__)}' finished with an invalid result after all attempts: {result}"
                )
            return result
        except (KeyboardInterrupt, SystemExit):
            raise
        except asyncio.TimeoutError as e:
            # Handles timeout specific to the total execution time (if self.policy.timeout is set)
            self._handle_final_failure(fn.__name__, e)
        except Exception as e:
            # Only handle exceptions listed in the policy; unlisted exceptions propagate immediately
            if not isinstance(e, self.policy.exceptions):
                raise
            self._handle_final_failure(fn.__name__, e)
