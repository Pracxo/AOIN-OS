"""Run supervision SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class RunSupervisionResource:
    """Client helpers for run supervision APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_run(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/run-supervision/runs", json=payload)

    def get_run(self, run_supervision_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/run-supervision/runs/{run_supervision_id}",
            params={"scope": list(scope)},
        )

    def list_runs(
        self,
        scope: Sequence[str],
        *,
        target_system: str | None = None,
        status: str | None = None,
        stalled: bool | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if target_system is not None:
            params["target_system"] = target_system
        if status is not None:
            params["status"] = status
        if stalled is not None:
            params["stalled"] = stalled
        return self._client.get("/brain/run-supervision/runs", params=params)

    def sample(self, run_supervision_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            f"/brain/run-supervision/runs/{run_supervision_id}/sample",
            json={"scope": list(scope)},
        )

    def sample_many(
        self, scope: Sequence[str], status: str | None = "active", limit: int = 100
    ) -> JSONValue:
        return self._client.post(
            "/brain/run-supervision/sample-many",
            json={"scope": list(scope), "status": status, "limit": limit},
        )

    def archive(
        self, run_supervision_id: str, reason: str, actor_id: str | None = None
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/run-supervision/runs/{run_supervision_id}/archive",
            json=payload,
        )

    def create_control_request(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/run-supervision/control-requests", json=payload)

    def list_control_requests(
        self,
        *,
        run_supervision_id: str | None = None,
        status: str | None = None,
        control_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if run_supervision_id is not None:
            params["run_supervision_id"] = run_supervision_id
        if status is not None:
            params["status"] = status
        if control_type is not None:
            params["control_type"] = control_type
        return self._client.get("/brain/run-supervision/control-requests", params=params)

    def handoff_control(
        self, run_control_request_id: str, approval_present: bool = False
    ) -> JSONValue:
        return self._client.post(
            f"/brain/run-supervision/control-requests/{run_control_request_id}/handoff",
            json={"approval_present": approval_present},
        )

    def create_timeout_policy(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/run-supervision/timeout-policies", json=payload)

    def list_timeout_policies(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        target_system: str | None = None,
        run_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope)}
        if status is not None:
            params["status"] = status
        if target_system is not None:
            params["target_system"] = target_system
        if run_type is not None:
            params["run_type"] = run_type
        return self._client.get("/brain/run-supervision/timeout-policies", params=params)

    def create_compensation_plan(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/run-supervision/compensation-plans", json=payload)

    def propose_compensation(self, run_supervision_id: str, trigger_reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/run-supervision/runs/{run_supervision_id}/propose-compensation",
            json={"trigger_reason": trigger_reason},
        )

    def get_compensation_plan(self, compensation_plan_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/run-supervision/compensation-plans/{compensation_plan_id}",
            params={"scope": list(scope)},
        )

    def list_compensation_plans(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        run_supervision_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if run_supervision_id is not None:
            params["run_supervision_id"] = run_supervision_id
        return self._client.get("/brain/run-supervision/compensation-plans", params=params)

    def approve_compensation_plan(
        self,
        compensation_plan_id: str,
        reason: str,
        approval_present: bool = False,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/run-supervision/compensation-plans/{compensation_plan_id}/approve",
            json={"reason": reason, "approval_present": approval_present},
        )

    def convert_compensation_to_action_proposals(
        self,
        compensation_plan_id: str,
        reason: str,
        approval_present: bool = False,
    ) -> JSONValue:
        return self._client.post(
            "/brain/run-supervision/compensation-plans/"
            f"{compensation_plan_id}/convert-to-action-proposals",
            json={"reason": reason, "approval_present": approval_present},
        )

    def create_report(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/run-supervision/reports", json=payload)


__all__ = ["RunSupervisionResource"]
