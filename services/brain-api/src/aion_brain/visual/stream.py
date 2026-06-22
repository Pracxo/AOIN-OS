"""SSE-compatible Visual Brain telemetry stream."""

import asyncio
import json
from collections.abc import AsyncIterator

from aion_brain.contracts.visual import VisualTelemetryQuery
from aion_brain.visual.service import VisualTelemetryQueryService


async def stream_visual_events(
    service: VisualTelemetryQueryService,
    query: VisualTelemetryQuery,
    poll_interval_seconds: float,
    max_events: int | None = None,
) -> AsyncIterator[str]:
    """Yield canonical visual telemetry in Server-Sent Events format."""
    emitted: set[str] = set()
    count = 0
    while max_events is None or count < max_events:
        try:
            events = list(reversed(service.query(query)))
            for event in events:
                if event.telemetry_id in emitted:
                    continue
                emitted.add(event.telemetry_id)
                data = {
                    "telemetry_id": event.telemetry_id,
                    "event_type": event.event_type,
                    "node_id": event.node_id,
                }
                serialized = json.dumps(data, separators=(",", ":"))
                yield f"event: visual_telemetry\ndata: {serialized}\n\n"
                count += 1
                if max_events is not None and count >= max_events:
                    return
        except Exception as exc:
            data = {"event_type": "observability_error", "message": str(exc)}
            yield f"event: observability_error\ndata: {json.dumps(data, separators=(',', ':'))}\n\n"
            count += 1
            if max_events is not None and count >= max_events:
                return
        await asyncio.sleep(max(0.01, poll_interval_seconds))
