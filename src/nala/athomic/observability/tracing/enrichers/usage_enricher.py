from nala.athomic.observability.tracing import get_current_span
from nala.athomic.observability.tracing.attributes import (
    UsageTracingAttributes,
)
from nala.athomic.usage.domain.events import UsageEvent


class UsageTracingEnricher:
    """
    Enriches the active tracing span with governed usage-related attributes.

    This enricher acts as an observability-side projection of the UsageEvent,
    mapping selected event fields into OpenTelemetry-compatible span attributes.
    It does not create or finalize spans and operates in a strict best-effort
    mode, ensuring zero impact on the execution flow.
    """

    def enrich(self, event: UsageEvent) -> None:
        """
        Attaches usage attributes to the current active span, if present.

        This method performs no action if no active span exists and never raises
        exceptions, preserving isolation between observability concerns and
        domain execution.
        """
        try:
            span = get_current_span()
            if span is None:
                return

            span.set_attribute(
                UsageTracingAttributes.SOURCE.value,
                event.source,
            )

            span.set_attribute(
                UsageTracingAttributes.UNIT.value,
                event.unit,
            )

            span.set_attribute(
                UsageTracingAttributes.QUANTITY.value,
                event.quantity,
            )

            if event.execution_id is not None:
                span.set_attribute(
                    UsageTracingAttributes.EXECUTION_ID.value,
                    event.execution_id,
                )

            if event.tenant_id is not None:
                span.set_attribute(
                    UsageTracingAttributes.TENANT_ID.value,
                    event.tenant_id,
                )

            if event.user_id is not None:
                span.set_attribute(
                    UsageTracingAttributes.USER_ID.value,
                    event.user_id,
                )

            if event.session_id is not None:
                span.set_attribute(
                    UsageTracingAttributes.SESSION_ID.value,
                    event.session_id,
                )

            if event.correlation_id is not None:
                span.set_attribute(
                    UsageTracingAttributes.CORRELATION_ID.value,
                    event.correlation_id,
                )
        except Exception:
            return
