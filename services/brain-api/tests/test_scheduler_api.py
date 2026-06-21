"""Scheduler API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from aion_brain.kernel.app_factory import create_app
from tests.kernel_fakes import kernel_container


def test_scheduler_api_create_list_tick_report() -> None:
    client = TestClient(create_app(kernel_container()))
    payload = {
        "schedule_id": "schedule-1",
        "name": "Review",
        "description": "Review local record.",
        "schedule_type": "reminder",
        "target_type": "reminder",
        "action_mode": "notify_only",
        "recurrence": {"frequency": "once"},
        "start_at": "2026-01-01T09:00:00Z",
        "owner_scope": ["workspace:main"],
    }

    created = client.post("/brain/scheduler/schedules", json=payload)
    listed = client.get("/brain/scheduler/schedules", params={"scope": "workspace:main"})
    tick = client.post(
        "/brain/scheduler/tick",
        json={
            "scope": ["workspace:main"],
            "mode": "controlled",
            "window_start": "2026-01-01T08:00:00Z",
            "window_end": "2026-01-01T10:00:00Z",
        },
    )
    report = client.post("/brain/scheduler/report", json={"scope": ["workspace:main"]})

    assert created.status_code == 200
    assert listed.status_code == 200
    assert tick.status_code == 200
    assert tick.json()["due_items_created"] == 1
    assert report.status_code == 200


def test_scheduler_api_reminder_lifecycle() -> None:
    client = TestClient(create_app(kernel_container()))

    created = client.post(
        "/brain/scheduler/reminders",
        json={
            "reminder_id": "reminder-1",
            "title": "Review",
            "message": "Review local reminder.",
            "due_at": "2026-01-01T09:00:00Z",
            "owner_scope": ["workspace:main"],
        },
    )
    acknowledged = client.post(
        "/brain/scheduler/reminders/reminder-1/acknowledge",
        params={"scope": "workspace:main"},
    )

    assert created.status_code == 200
    assert acknowledged.status_code == 200
    assert acknowledged.json()["status"] == "acknowledged"
