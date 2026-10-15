"""Stage 6 helper: send your agent's traces to Langfuse.

Strands emits OpenTelemetry (OTel) traces for every agent run: each model call,
each tool call (including the ones your ToolPolicy blocked), token counts and
latency. Langfuse is an open-source observability platform that accepts OTel, so
pointing Strands at it takes three settings: an endpoint, an auth header, and
turning the exporter on. Because it's OTel, the same traces could go to Jaeger,
Grafana, Datadog or AWS X-Ray instead.

Usage (in portal_agent.py, before you build any agent):
    from tracing import enable_langfuse_tracing
    enable_langfuse_tracing()
"""

import base64
import os

from config import LANGFUSE_HOST, LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY


def enable_langfuse_tracing(redact_phi: bool = False) -> bool:
    """Export this process's Strands traces to Langfuse. Returns True if tracing is on.

    Args:
        redact_phi: If True, replace prompts, replies and tool inputs/outputs in the
            traces with "[REDACTED]". Traces are data too: in a healthcare app they
            can hold PHI, so your observability stack needs the same care as your app.
    """
    if not (LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY):
        print("Langfuse keys not set: add langfuse_public_key and langfuse_secret_key to config.json.")
        return False

    # 1. Where to send traces. Langfuse's OTel endpoint lives under /api/public/otel.
    os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = f"{LANGFUSE_HOST.rstrip('/')}/api/public/otel"

    # 2. Optional: redact sensitive span attributes (an empty allowlist redacts all of them).
    if redact_phi:
        os.environ["OTEL_SEMCONV_STABILITY_OPT_IN"] = "gen_ai_unredacted_attributes="

    # 3. Authenticate with your project's keys (HTTP Basic auth), and turn the exporter on.
    from strands.telemetry import StrandsTelemetry

    token = base64.b64encode(f"{LANGFUSE_PUBLIC_KEY}:{LANGFUSE_SECRET_KEY}".encode()).decode()
    StrandsTelemetry().setup_otlp_exporter(headers={"Authorization": f"Basic {token}"})
    print(f"Tracing to Langfuse at {LANGFUSE_HOST}" + (" (PHI redacted)" if redact_phi else ""))
    return True
