"""Schedule metadata API tests."""

from datetime import UTC, datetime

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_schedule_service
from aion_brain.contracts.schedules import ScheduleCreateRequest, ScheduleRecord
from aion_brain.main import app


class FakeScheduleService:
    """Schedule service fake for API tests."""

    def __init__(self) -> None:
        self.schedules: dict[str, ScheduleRecord] = {"schedule-1": make_schedule("schedule-1")}

    def create_schedule(self, request: ScheduleCreateRequest) -> ScheduleRecord:
        schedule = make_schedule(
            request.schedule_id or "schedule-created",
            owner_type=request.owner_type,
            owner_id=request.owner_id,
            schedule_type=request.schedule_type,
        )
        self.schedules[schedule.schedule_id] = schedule
        return schedule

    def get_schedule(self, schedule_id: str) -> ScheduleRecord | None:
        return self.schedules.get(schedule_id)

    def list_schedules(
        self,
        owner_type: str | None = None,
        owner_id: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ScheduleRecord]:
        return [
            schedule
            for schedule in self.schedules.values()
            if (owner_type is None or schedule.owner_type == owner_type)
            and (owner_id is None or schedule.owner_id == owner_id)
            and (status is None or schedule.status == status)
        ][:limit]

    def pause_schedule(self, schedule_id: str) -> ScheduleRecord:
        schedule = self.schedules[schedule_id].model_copy(update={"status": "paused"})
        self.schedules[schedule_id] = schedule
        return schedule

    def cancel_schedule(self, schedule_id: str) -> ScheduleRecord:
        schedule = self.schedules[schedule_id].model_copy(update={"status": "cancelled"})
        self.schedules[schedule_id] = schedule
        return schedule


def test_schedules_api_create_get_list_pause_and_cancel() -> None:
    """Schedule endpoints expose metadata controls without worker actions."""
    service = FakeScheduleService()
    app.dependency_overrides[get_schedule_service] = lambda: service
    try:
        client = TestClient(app)
        created = client.post(
            "/brain/schedules",
            json={
                "schedule_id": "schedule-created",
                "owner_type": "task",
                "owner_id": "task-1",
                "schedule_type": "once",
                "schedule_expression": "2026-06-07T09:00:00Z",
            },
        )
        fetched = client.get("/brain/schedules/schedule-created")
        listed = client.get("/brain/schedules", params={"owner_type": "task"})
        paused = client.post("/brain/schedules/schedule-created/pause")
        cancelled = client.post("/brain/schedules/schedule-created/cancel")
    finally:
        app.dependency_overrides.clear()

    assert created.status_code == 200
    assert fetched.status_code == 200
    assert listed.status_code == 200
    assert paused.status_code == 200
    assert paused.json()["status"] == "paused"
    assert cancelled.status_code == 200
    assert cancelled.json()["status"] == "cancelled"


def make_schedule(
    schedule_id: str,
    *,
    owner_type: str = "task",
    owner_id: str = "task-1",
    schedule_type: str = "once",
) -> ScheduleRecord:
    """Create schedule metadata."""
    now = datetime.now(UTC)
    return ScheduleRecord(
        schedule_id=schedule_id,
        owner_type=owner_type,  # type: ignore[arg-type]
        owner_id=owner_id,
        schedule_type=schedule_type,  # type: ignore[arg-type]
        schedule_expression="2026-06-07T09:00:00Z",
        timezone="UTC",
        status="active",
        created_at=now,
        updated_at=now,
    )
