"""Explanation SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ExplanationsResource:
    """Client helpers for Explanation Engine APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def explain(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/explanations", json=payload)

    def get(self, explanation_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(f"/brain/explanations/{explanation_id}", params={"scope": scope})

    def list(
        self,
        *,
        trace_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 50,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if trace_id:
            params["trace_id"] = trace_id
        if target_type:
            params["target_type"] = target_type
        if target_id:
            params["target_id"] = target_id
        return self._client.get("/brain/explanations", params=params)

    def verify(self, explanation_id: str) -> JSONValue:
        return self._client.post(f"/brain/explanations/{explanation_id}/verify")

    def why_not(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/explanations/why-not", json=payload)

    def get_why_not(self, why_not_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/explanations/why-not/{why_not_id}",
            params={"scope": scope},
        )

    def trace_narrative(self, trace_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(f"/brain/traces/{trace_id}/narrative", json=payload)

    def get_trace_narrative(self, trace_narrative_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/traces/narratives/{trace_narrative_id}",
            params={"scope": scope},
        )

    def list_trace_narratives(self, trace_id: str, limit: int = 50) -> JSONValue:
        return self._client.get(
            f"/brain/traces/{trace_id}/narratives",
            params={"limit": limit},
        )

    def feedback(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/explanations/feedback", json=payload)

    def list_feedback(
        self,
        *,
        explanation_id: str | None = None,
        trace_narrative_id: str | None = None,
        why_not_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"limit": limit}
        if explanation_id:
            params["explanation_id"] = explanation_id
        if trace_narrative_id:
            params["trace_narrative_id"] = trace_narrative_id
        if why_not_id:
            params["why_not_id"] = why_not_id
        return self._client.get("/brain/explanations/feedback", params=params)


__all__ = ["ExplanationsResource"]
