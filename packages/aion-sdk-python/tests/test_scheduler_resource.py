from __future__ import annotations

from typing import Any

import httpx

from aion_sdk import AIONClient, AIONClientConfig


def _client(handler: Any) -> AIONClient:
    return AIONClient(
        AIONClientConfig(base_url="http://aion.test"),
        httpx.Client(transport=httpx.MockTransport(handler)),
    )


def test_scheduler_resource_calls_expected_endpoints() -> None:
    seen: list[tuple[str, str]] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append((request.method, request.url.path))
        return httpx.Response(200, json={"ok": True})

    client = _client(handler)
    client.scheduler.create_schedule({"schedule_id": "schedule-1"})
    client.scheduler.get_schedule("schedule-1", ["workspace:main"])
    client.scheduler.list_schedules(["workspace:main"])
    client.scheduler.pause_schedule("schedule-1", ["workspace:main"])
    client.scheduler.resume_schedule("schedule-1", ["workspace:main"])
    client.scheduler.disable_schedule("schedule-1", ["workspace:main"])
    client.scheduler.delete_schedule("schedule-1", ["workspace:main"])
    client.scheduler.list_due_items(["workspace:main"])
    client.scheduler.create_reminder({"reminder_id": "reminder-1"})
    client.scheduler.list_reminders(["workspace:main"])
    client.scheduler.acknowledge_reminder("reminder-1", ["workspace:main"])
    client.scheduler.snooze_reminder("reminder-1", ["workspace:main"], "2026-01-01T10:00:00Z")
    client.scheduler.dismiss_reminder("reminder-1", ["workspace:main"])
    client.scheduler.run_tick({"scope": ["workspace:main"]})
    client.scheduler.get_tick_run("tick-1", ["workspace:main"])
    client.scheduler.create_policy({"policy_id": "policy-1"})
    client.scheduler.list_policies(["workspace:main"])
    client.scheduler.create_report(["workspace:main"])

    assert seen == [
        ("POST", "/brain/scheduler/schedules"),
        ("GET", "/brain/scheduler/schedules/schedule-1"),
        ("GET", "/brain/scheduler/schedules"),
        ("POST", "/brain/scheduler/schedules/schedule-1/pause"),
        ("POST", "/brain/scheduler/schedules/schedule-1/resume"),
        ("POST", "/brain/scheduler/schedules/schedule-1/disable"),
        ("DELETE", "/brain/scheduler/schedules/schedule-1"),
        ("GET", "/brain/scheduler/due-items"),
        ("POST", "/brain/scheduler/reminders"),
        ("GET", "/brain/scheduler/reminders"),
        ("POST", "/brain/scheduler/reminders/reminder-1/acknowledge"),
        ("POST", "/brain/scheduler/reminders/reminder-1/snooze"),
        ("POST", "/brain/scheduler/reminders/reminder-1/dismiss"),
        ("POST", "/brain/scheduler/tick"),
        ("GET", "/brain/scheduler/tick-runs/tick-1"),
        ("POST", "/brain/scheduler/policies"),
        ("GET", "/brain/scheduler/policies"),
        ("POST", "/brain/scheduler/report"),
    ]


def test_scheduler_resource_does_not_import_brain_package() -> None:
    import aion_sdk.resources.scheduler as resource

    assert "aion_brain" not in resource.__dict__
