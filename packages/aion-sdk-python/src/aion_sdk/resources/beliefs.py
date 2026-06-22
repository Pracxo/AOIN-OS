"""Beliefs SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class BeliefsResource:
    """Client helpers for belief APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_claim(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/beliefs/claims", json=payload)

    def get_claim(self, claim_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(f"/brain/beliefs/claims/{claim_id}", params={"scope": scope})

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/beliefs/query", json=payload)

    def revise_claim(self, claim_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(f"/brain/beliefs/claims/{claim_id}/revise", json=payload)

    def create_support(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/beliefs/supports", json=payload)

    def list_supports(self, claim_id: str) -> JSONValue:
        return self._client.get(f"/brain/beliefs/claims/{claim_id}/supports")

    def list_contradictions(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status is not None:
            params["status"] = status
        if severity is not None:
            params["severity"] = severity
        return self._client.get("/brain/beliefs/contradictions", params=params)

    def resolve_contradiction(self, contradiction_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/beliefs/contradictions/{contradiction_id}/resolve",
            json={"reason": reason},
        )

    def extract(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/beliefs/extract", json=payload)

    def run_truth_maintenance(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/beliefs/truth-maintenance/run", json=payload)

    def get_truth_maintenance(self, truth_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/beliefs/truth-maintenance/{truth_run_id}")
