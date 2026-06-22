"""Release candidate SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ReleaseCandidateResource:
    """Client helpers for release candidate gate APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_candidate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/rc/candidates", json=payload)

    def list_candidates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        version: str | None = None,
        release_ready: bool | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "version", version)
        _set(params, "release_ready", release_ready)
        return self._client.get("/brain/rc/candidates", params=params)

    def get_candidate(self, release_candidate_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/rc/candidates/{release_candidate_id}",
            params={"scope": list(scope)},
        )

    def create_matrix(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/rc/matrices", json=payload)

    def list_matrices(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        return self._client.get("/brain/rc/matrices", params=params)

    def seed_default_matrices(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
        created_by: str | None = None,
    ) -> JSONValue:
        return self._client.post(
            "/brain/rc/matrices/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run, "created_by": created_by},
        )

    def run_gate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/rc/gate/run", json=payload)

    def get_run(self, rc_run_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/rc/gate/runs/{rc_run_id}",
            params={"scope": list(scope)},
        )

    def list_findings(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        blocking: bool | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "severity", severity)
        _set(params, "blocking", blocking)
        return self._client.get("/brain/rc/findings", params=params)

    def dismiss_finding(
        self,
        rc_finding_id: str,
        scope: Sequence[str],
        *,
        reason: str = "dismissed",
    ) -> JSONValue:
        return self._client.post(
            f"/brain/rc/findings/{rc_finding_id}/dismiss",
            params={"scope": list(scope)},
            json={"reason": reason},
        )

    def list_evidence_packs(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        return self._client.get("/brain/rc/evidence-packs", params=params)

    def get_evidence_pack(self, evidence_pack_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/rc/evidence-packs/{evidence_pack_id}",
            params={"scope": list(scope)},
        )

    def list_reports(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        version: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        _set(params, "status", status)
        _set(params, "version", version)
        return self._client.get("/brain/rc/reports", params=params)

    def get_report(self, rc_report_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/rc/reports/{rc_report_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/rc/query", json=payload)


def _set(params: dict[str, object], key: str, value: object | None) -> None:
    if value is not None:
        params[key] = value


__all__ = ["ReleaseCandidateResource"]
