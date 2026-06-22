"""Data lifecycle SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class LifecycleResource:
    """Client helpers for advisory lifecycle APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_policy(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/lifecycle/policies", json=payload)

    def seed_default_policies(
        self,
        scope: Sequence[str],
        *,
        dry_run: bool = True,
    ) -> JSONValue:
        return self._client.post(
            "/brain/lifecycle/policies/seed-defaults",
            json={"scope": list(scope), "dry_run": dry_run},
        )

    def list_policies(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        policy_type: str | None = None,
        retention_class: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if policy_type is not None:
            params["policy_type"] = policy_type
        if retention_class is not None:
            params["retention_class"] = retention_class
        return self._client.get("/brain/lifecycle/policies", params=params)

    def get_policy(self, lifecycle_policy_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/lifecycle/policies/{lifecycle_policy_id}",
            params={"scope": list(scope)},
        )

    def evaluate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/lifecycle/evaluate", json=payload)

    def get_evaluation(self, lifecycle_evaluation_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/lifecycle/evaluations/{lifecycle_evaluation_id}",
            params={"scope": list(scope)},
        )

    def list_classifications(
        self,
        scope: Sequence[str],
        *,
        retention_class: str | None = None,
        lifecycle_state: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if retention_class is not None:
            params["retention_class"] = retention_class
        if lifecycle_state is not None:
            params["lifecycle_state"] = lifecycle_state
        return self._client.get("/brain/lifecycle/classifications", params=params)

    def list_archive_candidates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self._candidate_list(
            "/brain/lifecycle/archive-candidates",
            scope,
            status=status,
            severity=severity,
            limit=limit,
        )

    def dismiss_archive_candidate(
        self,
        archive_candidate_id: str,
        reason: str,
        *,
        actor_id: str | None = None,
    ) -> JSONValue:
        return self._candidate_mutation(
            f"/brain/lifecycle/archive-candidates/{archive_candidate_id}/dismiss",
            reason,
            actor_id=actor_id,
        )

    def convert_archive_candidate(
        self,
        archive_candidate_id: str,
        reason: str,
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
    ) -> JSONValue:
        return self._candidate_mutation(
            f"/brain/lifecycle/archive-candidates/{archive_candidate_id}/convert-to-action-proposal",
            reason,
            actor_id=actor_id,
            approval_present=approval_present,
        )

    def list_redaction_candidates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        return self._candidate_list(
            "/brain/lifecycle/redaction-candidates",
            scope,
            status=status,
            severity=severity,
            limit=limit,
        )

    def dismiss_redaction_candidate(
        self,
        redaction_candidate_id: str,
        reason: str,
        *,
        actor_id: str | None = None,
    ) -> JSONValue:
        return self._candidate_mutation(
            f"/brain/lifecycle/redaction-candidates/{redaction_candidate_id}/dismiss",
            reason,
            actor_id=actor_id,
        )

    def convert_redaction_candidate(
        self,
        redaction_candidate_id: str,
        reason: str,
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
    ) -> JSONValue:
        return self._candidate_mutation(
            f"/brain/lifecycle/redaction-candidates/{redaction_candidate_id}/convert-to-action-proposal",
            reason,
            actor_id=actor_id,
            approval_present=approval_present,
        )

    def create_purge_preview(
        self,
        resource_uris: Sequence[str],
        scope: Sequence[str],
        *,
        trace_id: str | None = None,
        created_by: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"resource_uris": list(resource_uris), "scope": list(scope)}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        if created_by is not None:
            payload["created_by"] = created_by
        return self._client.post("/brain/lifecycle/purge-preview", json=payload)

    def list_purge_previews(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        return self._client.get("/brain/lifecycle/purge-previews", params=params)

    def review_candidate(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/lifecycle/reviews", json=payload)

    def list_reviews(
        self,
        scope: Sequence[str],
        *,
        candidate_type: str | None = None,
        decision: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if candidate_type is not None:
            params["candidate_type"] = candidate_type
        if decision is not None:
            params["decision"] = decision
        return self._client.get("/brain/lifecycle/reviews", params=params)

    def report(
        self,
        scope: Sequence[str],
        *,
        trace_id: str | None = None,
        created_by: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"scope": list(scope)}
        if trace_id is not None:
            payload["trace_id"] = trace_id
        if created_by is not None:
            payload["created_by"] = created_by
        return self._client.post("/brain/lifecycle/report", json=payload)

    def _candidate_list(
        self,
        path: str,
        scope: Sequence[str],
        *,
        status: str | None,
        severity: str | None,
        limit: int,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        return self._client.get(path, params=params)

    def _candidate_mutation(
        self,
        path: str,
        reason: str,
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason, "approval_present": approval_present}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(path, json=payload)


__all__ = ["LifecycleResource"]
