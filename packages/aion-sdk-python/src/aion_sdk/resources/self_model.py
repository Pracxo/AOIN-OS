"""Self-model SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class SelfModelResource:
    """Client helpers for AION self-model APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def describe(
        self,
        scope: list[str],
        *,
        include_capabilities: bool = True,
        include_limitations: bool = True,
        format: str = "structured",
    ) -> JSONValue:
        return self._client.get(
            "/brain/self",
            params={
                "scope": scope,
                "include_capabilities": include_capabilities,
                "include_limitations": include_limitations,
                "format": format,
            },
        )

    def capabilities(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        capability_type: str | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if status:
            params["status"] = status
        if capability_type:
            params["capability_type"] = capability_type
        return self._client.get("/brain/self/capabilities", params=params)

    def refresh_capabilities(self, scope: list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/self/capabilities/refresh",
            json={"scope": scope, "dry_run": dry_run},
        )

    def create_limitation(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/self/limitations", json=payload)

    def list_limitations(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        category: str | None = None,
        severity: str | None = None,
        disclosure_required: bool | None = None,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        if status:
            params["status"] = status
        if category:
            params["category"] = category
        if severity:
            params["severity"] = severity
        if disclosure_required is not None:
            params["disclosure_required"] = disclosure_required
        return self._client.get("/brain/self/limitations", params=params)

    def seed_limitations(self, scope: list[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/self/limitations/seed-defaults",
            json={"scope": scope, "dry_run": dry_run},
        )

    def resolve_limitation(self, limitation_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/self/limitations/{limitation_id}/resolve",
            json={"reason": reason},
        )

    def calibrate_confidence(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/self/confidence/calibrate", json=payload)

    def list_confidence(
        self,
        *,
        trace_id: str | None = None,
        response_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if response_id:
            params["response_id"] = response_id
        return self._client.get("/brain/self/confidence", params=params)

    def run_assessment(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/self/assessment/run", json=payload)

    def get_assessment(self, self_assessment_id: str) -> JSONValue:
        return self._client.get(f"/brain/self/assessment/{self_assessment_id}")

    def create_introspection(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/self/introspection", json=payload)

    def get_introspection(self, introspection_snapshot_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/self/introspection/{introspection_snapshot_id}",
            params={"scope": scope},
        )

    def list_introspection(
        self,
        scope: list[str],
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if snapshot_type:
            params["snapshot_type"] = snapshot_type
        if status:
            params["status"] = status
        return self._client.get("/brain/self/introspection", params=params)


__all__ = ["SelfModelResource"]
