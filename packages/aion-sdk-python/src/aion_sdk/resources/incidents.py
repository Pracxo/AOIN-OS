"""Incident correlation SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class IncidentsResource:
    """Client helpers for incident correlation APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_signal(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/signals", json=payload)

    def list_signals(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        source_type: str | None = None,
        signal_type: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if source_type is not None:
            params["source_type"] = source_type
        if signal_type is not None:
            params["signal_type"] = signal_type
        if severity is not None:
            params["severity"] = severity
        return self._client.get("/brain/incidents/signals", params=params)

    def dismiss_signal(self, incident_signal_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/incidents/signals/{incident_signal_id}/dismiss",
            json={"reason": reason},
        )

    def create_incident(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents", json=payload)

    def get_incident(self, incident_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/incidents/{incident_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/query", json=payload)

    def acknowledge(self, incident_id: str, reason: str) -> JSONValue:
        return self._incident_update(incident_id, "acknowledge", reason)

    def resolve(self, incident_id: str, reason: str) -> JSONValue:
        return self._incident_update(incident_id, "resolve", reason)

    def dismiss(self, incident_id: str, reason: str) -> JSONValue:
        return self._incident_update(incident_id, "dismiss", reason)

    def archive(self, incident_id: str, reason: str) -> JSONValue:
        return self._incident_update(incident_id, "archive", reason)

    def create_rule(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/rules", json=payload)

    def list_rules(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if rule_type is not None:
            params["rule_type"] = rule_type
        return self._client.get("/brain/incidents/rules", params=params)

    def seed_rules(self, scope: Sequence[str], dry_run: bool = True) -> JSONValue:
        return self._client.post(
            "/brain/incidents/rules/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run},
        )

    def correlate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/correlate", json=payload)

    def get_correlation_run(self, correlation_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/incidents/correlation-runs/{correlation_run_id}")

    def generate_root_causes(self, incident_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.post(
            f"/brain/incidents/{incident_id}/root-cause-candidates/generate",
            json={"scope": list(scope)},
        )

    def create_root_cause(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/root-cause-candidates", json=payload)

    def list_root_causes(
        self,
        incident_id: str | None = None,
        *,
        status: str | None = None,
        candidate_type: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if incident_id is not None:
            params["incident_id"] = incident_id
        if status is not None:
            params["status"] = status
        if candidate_type is not None:
            params["candidate_type"] = candidate_type
        return self._client.get("/brain/incidents/root-cause-candidates", params=params)

    def confirm_root_cause(self, root_cause_candidate_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/incidents/root-cause-candidates/{root_cause_candidate_id}/confirm",
            json={"reason": reason},
        )

    def dismiss_root_cause(self, root_cause_candidate_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/incidents/root-cause-candidates/{root_cause_candidate_id}/dismiss",
            json={"reason": reason},
        )

    def create_recovery_review(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/incidents/recovery-reviews", json=payload)

    def get_recovery_review(self, recovery_review_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/incidents/recovery-reviews/{recovery_review_id}",
            params={"scope": list(scope)},
        )

    def list_recovery_reviews(
        self,
        scope: Sequence[str],
        *,
        incident_id: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if incident_id is not None:
            params["incident_id"] = incident_id
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/incidents/recovery-reviews", params=params)

    def _incident_update(self, incident_id: str, action: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/incidents/{incident_id}/{action}",
            json={"reason": reason},
        )


__all__ = ["IncidentsResource"]
