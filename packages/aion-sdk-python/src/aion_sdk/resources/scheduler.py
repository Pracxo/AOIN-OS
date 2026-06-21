"""Temporal Scheduler SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class SchedulerResource:
    """Client helpers for local scheduler APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_schedule(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scheduler/schedules", json=payload)

    def get_schedule(self, schedule_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/scheduler/schedules/{schedule_id}",
            params={"scope": list(scope)},
        )

    def list_schedules(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        schedule_type: str | None = None,
        target_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if schedule_type is not None:
            params["schedule_type"] = schedule_type
        if target_type is not None:
            params["target_type"] = target_type
        return self._client.get("/brain/scheduler/schedules", params=params)

    def pause_schedule(
        self, schedule_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._schedule_update(schedule_id, "pause", scope)

    def resume_schedule(
        self, schedule_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._schedule_update(schedule_id, "resume", scope)

    def disable_schedule(
        self, schedule_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._schedule_update(schedule_id, "disable", scope)

    def delete_schedule(
        self, schedule_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._client.delete(
            f"/brain/scheduler/schedules/{schedule_id}",
            params={"scope": list(scope)},
        )

    def list_due_items(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        schedule_id: str | None = None,
        missed: bool | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if schedule_id is not None:
            params["schedule_id"] = schedule_id
        if missed is not None:
            params["missed"] = missed
        return self._client.get("/brain/scheduler/due-items", params=params)

    def create_reminder(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scheduler/reminders", json=payload)

    def list_reminders(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        reminder_type: str | None = None,
        actor_id: str | None = None,
        workspace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if reminder_type is not None:
            params["reminder_type"] = reminder_type
        if actor_id is not None:
            params["actor_id"] = actor_id
        if workspace_id is not None:
            params["workspace_id"] = workspace_id
        return self._client.get("/brain/scheduler/reminders", params=params)

    def acknowledge_reminder(
        self, reminder_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._reminder_update(reminder_id, "acknowledge", scope)

    def dismiss_reminder(
        self, reminder_id: str, scope: Sequence[str], reason: str | None = None
    ) -> JSONValue:
        return self._reminder_update(reminder_id, "dismiss", scope)

    def snooze_reminder(
        self,
        reminder_id: str,
        scope: Sequence[str],
        snoozed_until: str,
        reason: str | None = None,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/scheduler/reminders/{reminder_id}/snooze",
            params={"scope": list(scope)},
            json={"snoozed_until": snoozed_until},
        )

    def run_tick(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scheduler/tick", json=payload)

    def tick(self, payload: JSONDict) -> JSONValue:
        return self.run_tick(payload)

    def get_tick_run(self, tick_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/scheduler/tick-runs/{tick_run_id}",
            params={"scope": list(scope)},
        )

    def create_policy(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/scheduler/policies", json=payload)

    def list_policies(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        policy_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if policy_type is not None:
            params["policy_type"] = policy_type
        return self._client.get("/brain/scheduler/policies", params=params)

    def create_report(self, scope: Sequence[str], trace_id: str | None = None) -> JSONValue:
        payload: dict[str, object] = {"scope": list(scope)}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        return self._client.post("/brain/scheduler/report", json=payload)

    def report(self, scope: Sequence[str], trace_id: str | None = None) -> JSONValue:
        return self.create_report(scope, trace_id=trace_id)

    def _schedule_update(self, schedule_id: str, action: str, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            f"/brain/scheduler/schedules/{schedule_id}/{action}",
            params={"scope": list(scope)},
        )

    def _reminder_update(self, reminder_id: str, action: str, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            f"/brain/scheduler/reminders/{reminder_id}/{action}",
            params={"scope": list(scope)},
        )


__all__ = ["SchedulerResource"]
