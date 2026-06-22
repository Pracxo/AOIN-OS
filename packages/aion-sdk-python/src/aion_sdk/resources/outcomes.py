"""Outcome ledger SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class OutcomesResource:
    """Client helpers for outcome ledger APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes", json=payload)

    def get(self, outcome_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(f"/brain/outcomes/{outcome_id}", params={"scope": scope})

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/query", json=payload)

    def close(self, outcome_id: str, reason: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/outcomes/{outcome_id}/close",
            params={"scope": scope},
            json={"reason": reason},
        )

    def create_expected_effect(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/expected-effects", json=payload)

    def list_expected_effects(
        self,
        *,
        source_type: str | None = None,
        source_id: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if source_type:
            params["source_type"] = source_type
        if source_id:
            params["source_id"] = source_id
        if trace_id:
            params["trace_id"] = trace_id
        return self._client.get("/brain/outcomes/expected-effects", params=params)

    def create_observed_effect(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/observed-effects", json=payload)

    def list_observed_effects(
        self,
        *,
        outcome_id: str | None = None,
        source_type: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if outcome_id:
            params["outcome_id"] = outcome_id
        if source_type:
            params["source_type"] = source_type
        if source_id:
            params["source_id"] = source_id
        return self._client.get("/brain/outcomes/observed-effects", params=params)

    def verify(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/verify", json=payload)

    def get_verification(self, verification_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/outcomes/verifications/{verification_run_id}")

    def create_attribution(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/attributions", json=payload)

    def list_attributions(
        self,
        *,
        outcome_id: str | None = None,
        cause_type: str | None = None,
        cause_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if outcome_id:
            params["outcome_id"] = outcome_id
        if cause_type:
            params["cause_type"] = cause_type
        if cause_id:
            params["cause_id"] = cause_id
        return self._client.get("/brain/outcomes/attributions", params=params)

    def create_feedback(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/outcomes/feedback", json=payload)

    def list_feedback(
        self,
        *,
        outcome_id: str | None = None,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if outcome_id:
            params["outcome_id"] = outcome_id
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        return self._client.get("/brain/outcomes/feedback", params=params)

    def resolve_feedback(self, outcome_feedback_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/outcomes/feedback/{outcome_feedback_id}/resolve",
            json={"reason": reason},
        )

    def learning_bridge(self, outcome_id: str, dry_run: bool = True) -> JSONValue:
        return self._client.post(
            f"/brain/outcomes/{outcome_id}/learning-bridge",
            json={"dry_run": dry_run},
        )


__all__ = ["OutcomesResource"]
