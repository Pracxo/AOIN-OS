"""Module activation request gate SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModuleActivationResource:
    """Client helpers for metadata-only module activation gate APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_request(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-activation/requests", json=payload)

    def list_requests(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "module_slot_id", module_slot_id)
        return self._client.get("/brain/module-activation/requests", params=params)

    def get_request(self, activation_request_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-activation/requests/{activation_request_id}",
            params={"scope": list(scope)},
        )

    def archive_request(
        self,
        activation_request_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-activation/requests/{activation_request_id}/archive",
            json=payload,
        )

    def delete_request(
        self,
        activation_request_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.delete(
            f"/brain/module-activation/requests/{activation_request_id}",
            json=payload,
        )

    def run_gate(
        self,
        activation_request_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-activation/requests/{activation_request_id}/gate",
            json=payload,
        )

    def list_gate_runs(
        self,
        activation_request_id: str,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        return self._client.get(
            f"/brain/module-activation/requests/{activation_request_id}/gate-runs",
            params=params,
        )

    def list_blockers(
        self,
        scope: Sequence[str],
        *,
        activation_request_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "activation_request_id", activation_request_id)
        _set(params, "status", status)
        _set(params, "severity", severity)
        return self._client.get("/brain/module-activation/blockers", params=params)

    def dismiss_blocker(
        self,
        activation_blocker_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-activation/blockers/{activation_blocker_id}/dismiss",
            json=payload,
        )

    def create_review(
        self,
        payload: JSONDict,
        scope: Sequence[str] = (),
    ) -> JSONValue:
        return self._client.post(
            "/brain/module-activation/reviews",
            json=payload,
            params={"scope": list(scope)},
        )

    def list_reviews(
        self,
        scope: Sequence[str],
        *,
        activation_request_id: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "activation_request_id", activation_request_id)
        _set(params, "decision", decision)
        return self._client.get("/brain/module-activation/reviews", params=params)

    def create_plan(
        self,
        activation_request_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-activation/requests/{activation_request_id}/plans",
            json=payload,
        )

    def list_plans(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        module_slot_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "module_slot_id", module_slot_id)
        return self._client.get("/brain/module-activation/plans", params=params)

    def get_plan(self, activation_plan_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/module-activation/plans/{activation_plan_id}",
            params={"scope": list(scope)},
        )

    def create_runtime_registration_preview(
        self,
        activation_request_id: str,
        payload: JSONDict,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/module-activation/requests/{activation_request_id}/runtime-registration-preview",
            json=payload,
        )

    def list_runtime_registration_previews(
        self,
        scope: Sequence[str],
        *,
        activation_request_id: str | None = None,
        module_slot_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "activation_request_id", activation_request_id)
        _set(params, "module_slot_id", module_slot_id)
        _set(params, "status", status)
        return self._client.get(
            "/brain/module-activation/runtime-registration-previews",
            params=params,
        )

    def get_runtime_registration_preview(
        self,
        registration_preview_id: str,
        scope: Sequence[str],
    ) -> JSONValue:
        return self._client.get(
            f"/brain/module-activation/runtime-registration-previews/{registration_preview_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/module-activation/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ModuleActivationResource"]
