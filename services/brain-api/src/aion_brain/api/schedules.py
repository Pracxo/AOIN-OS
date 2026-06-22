"""Schedule metadata API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.dependencies import get_schedule_service
from aion_brain.contracts.schedules import ScheduleCreateRequest, ScheduleRecord
from aion_brain.schedules.service import ScheduleService

router = APIRouter(prefix="/brain/schedules", tags=["schedules"])


@router.post("", response_model=ScheduleRecord)
def create_schedule(
    request: ScheduleCreateRequest,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleRecord:
    """Create schedule metadata."""
    try:
        return service.create_schedule(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.get("/{schedule_id}", response_model=ScheduleRecord)
def get_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleRecord:
    """Return schedule metadata."""
    schedule = service.get_schedule(schedule_id)
    if schedule is None:
        raise HTTPException(status_code=404, detail="schedule_not_found")
    return schedule


@router.get("", response_model=list[ScheduleRecord])
def list_schedules(
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
    owner_type: str | None = None,
    owner_id: str | None = None,
    status: str | None = None,
    limit: int = 50,
) -> list[ScheduleRecord]:
    """List schedule metadata."""
    return service.list_schedules(
        owner_type=owner_type,
        owner_id=owner_id,
        status=status,
        limit=limit,
    )


@router.post("/{schedule_id}/pause", response_model=ScheduleRecord)
def pause_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleRecord:
    """Pause schedule metadata."""
    try:
        return service.pause_schedule(schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/{schedule_id}/cancel", response_model=ScheduleRecord)
def cancel_schedule(
    schedule_id: str,
    service: Annotated[ScheduleService, Depends(get_schedule_service)],
) -> ScheduleRecord:
    """Cancel schedule metadata."""
    try:
        return service.cancel_schedule(schedule_id)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
