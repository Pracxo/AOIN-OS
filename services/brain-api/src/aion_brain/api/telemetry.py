"""Visual telemetry API."""

from typing import Annotated

from fastapi import APIRouter, Depends

from aion_brain.api.dependencies import get_audit_repository
from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.telemetry import VisualTelemetryEvent

router = APIRouter(prefix="/brain", tags=["telemetry"])


@router.get("/traces/{trace_id}/telemetry", response_model=list[VisualTelemetryEvent])
def list_trace_telemetry(
    trace_id: str,
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> list[VisualTelemetryEvent]:
    """Return visual telemetry events for a trace."""
    return repository.list_visual_telemetry(trace_id)
