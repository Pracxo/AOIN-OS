"""Local observability recorder."""

from datetime import UTC, datetime

from aion_brain.contracts.observability import ObservabilityEvent, ObservabilitySummary
from aion_brain.contracts.visual import VisualTelemetryQuery
from aion_brain.observability.repository import ObservabilityRepository
from aion_brain.visual.repository import VisualRepository


class LocalObservabilityRecorder:
    """Record and summarize observability without external calls."""

    def __init__(
        self,
        repository: ObservabilityRepository,
        visual_repository: VisualRepository,
    ) -> None:
        self._repository = repository
        self._visual_repository = visual_repository

    def record_event(self, event: ObservabilityEvent) -> ObservabilityEvent:
        """Persist a sanitized event locally."""
        return self._repository.save(event)

    def summarize(self, scope: list[str]) -> ObservabilitySummary:
        """Return a summary of local observability and telemetry."""
        observability_events = self._repository.list_events(limit=1000)
        telemetry = self._visual_repository.query_telemetry(
            VisualTelemetryQuery(scope=scope, limit=1000)
        )
        trace_ids = {
            trace_id
            for trace_id in [
                *(event.trace_id for event in observability_events),
                *(event.trace_id for event in telemetry),
            ]
            if trace_id
        }
        latest_trace_id = next(
            (event.trace_id for event in observability_events if event.trace_id),
            next((event.trace_id for event in telemetry if event.trace_id), None),
        )
        return ObservabilitySummary(
            trace_count=len(trace_ids),
            telemetry_event_count=len(telemetry),
            observability_event_count=len(observability_events),
            active_node_count=len({event.node_id for event in telemetry}),
            blocked_event_count=sum("blocked" in event.event_type for event in telemetry)
            + sum(event.level == "warning" for event in observability_events),
            failed_event_count=sum("failed" in event.event_type for event in telemetry)
            + sum(event.level == "error" for event in observability_events),
            latest_trace_id=latest_trace_id,
            generated_at=datetime.now(UTC),
        )
