import os

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor


def init_instrumentation(app: FastAPI) -> None:
    tracer_provider = TracerProvider()
    trace.set_tracer_provider(tracer_provider)

    otlp_exporter = OTLPSpanExporter(
        endpoint=os.environ.get("OTLP_ENDPOINT", "localhost:4317"),
        insecure=True,
    )

    span_processor = BatchSpanProcessor(otlp_exporter)
    tracer_provider.add_span_processor(span_processor)

    FastAPIInstrumentor.instrument_app(app)
