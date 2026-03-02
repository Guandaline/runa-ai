import httpx
import pytest
import respx
from opentelemetry import trace
from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

from nala.athomic.config import settings
from nala.athomic.observability.tracing.tracing import setup_tracing


@pytest.fixture(autouse=True)
def initial_tracing_setup():
    app_settings = settings.get_settings()
    if app_settings.observability.tracing_enabled:
        setup_tracing(app_settings)
    yield


async def function_that_makes_a_call():
    async with httpx.AsyncClient() as client:
        await client.get("http://some-external-service.com/data")


@respx.mock
@pytest.mark.asyncio
async def test_trace_is_propagated_from_manual_span():
    HTTPXClientInstrumentor().uninstrument()
    HTTPXClientInstrumentor().instrument()

    external_url = "http://some-external-service.com/data"
    received_headers = {}

    def capture_headers(request: httpx.Request):
        nonlocal received_headers
        received_headers.update(request.headers)
        return httpx.Response(200, json={"ok": True})

    respx.get(external_url).mock(side_effect=capture_headers)

    tracer = trace.get_tracer("athomic.test.tracer")
    with tracer.start_as_current_span("test-parent-span") as parent_span:
        await function_that_makes_a_call()
        assert "traceparent" in received_headers
        parent_trace_id = f"{parent_span.get_span_context().trace_id:032x}"
        propagated_trace_id = received_headers["traceparent"].split("-")[1]
        assert propagated_trace_id == parent_trace_id

    HTTPXClientInstrumentor().uninstrument()
