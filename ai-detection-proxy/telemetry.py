# pyrefly: ignore [missing-import]
from opentelemetry import trace
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace import TracerProvider
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.trace.export import BatchSpanProcessor
# pyrefly: ignore [missing-import]
from opentelemetry.sdk.resources import Resource
# pyrefly: ignore [missing-import]
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os

load_dotenv()

def setup_telemetry(service_name: str = "ai-detection-proxy"):
    """
    Настройка OpenTelemetry.
    Span'ы отправляются в Splunk Observability Cloud через OTLP/HTTP.
    """
    realm = os.getenv("SPLUNK_REALM", "eu1")
    token = os.getenv("SPLUNK_TOKEN")

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)

    exporter = OTLPSpanExporter(
        endpoint=f"https://ingest.{realm}.signalfx.com/v2/trace/otlp",
        headers={"X-SF-Token": token},
    )

    provider.add_span_processor(BatchSpanProcessor(exporter))
    trace.set_tracer_provider(provider)

    return trace.get_tracer(service_name)

