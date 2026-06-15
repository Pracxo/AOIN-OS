"""Visual SSE stream tests."""

import asyncio

from aion_brain.contracts.visual import VisualTelemetryQuery
from aion_brain.visual.stream import stream_visual_events
from tests.test_visual_service import telemetry


class FakeQueryService:
    """Query service fake."""

    def query(self, query: VisualTelemetryQuery):
        return [telemetry()]


def test_visual_stream_yields_valid_sse_and_stops_at_max_events() -> None:
    """The SSE stream emits valid JSON data and terminates for tests."""

    async def collect() -> list[str]:
        return [
            item
            async for item in stream_visual_events(
                FakeQueryService(),  # type: ignore[arg-type]
                VisualTelemetryQuery(scope=["workspace:main"]),
                0.01,
                max_events=1,
            )
        ]

    events = asyncio.run(collect())
    assert len(events) == 1
    assert events[0].startswith("event: visual_telemetry\ndata: {")
    assert events[0].endswith("\n\n")
