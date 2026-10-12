"""Structured JSON logs and OpenTelemetry tracing."""
import json, logging, sys, time
from contextlib import contextmanager
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("apex")
log = logging.getLogger("apex"); log.setLevel(logging.INFO)
h = logging.StreamHandler(sys.stdout); h.setFormatter(logging.Formatter("%(message)s")); log.addHandler(h)

@contextmanager
def run_span(name, **attrs):
    t0 = time.perf_counter()
    with tracer.start_as_current_span(name):
        yield
    log.info(json.dumps({"span": name, "latency_ms": round((time.perf_counter() - t0) * 1000, 1), **attrs}))
