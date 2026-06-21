"""Model output governance SDK resource."""

from __future__ import annotations

from collections.abc import Sequence
from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class ModelOutputsResource:
    """Client helpers for model output governance APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-outputs", json=payload)

    def get(self, model_output_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/model-outputs/{model_output_id}",
            params={"scope": list(scope)},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/model-outputs/query", json=payload)

    def delete(self, model_output_id: str, reason: str, actor_id: str | None = None) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.delete(f"/brain/model-outputs/{model_output_id}", json=payload)

    def govern(self, model_output_id: str, payload: JSONDict) -> JSONValue:
        return self._client.post(f"/brain/model-outputs/{model_output_id}/govern", json=payload)

    def get_governance(self, output_governance_id: str) -> JSONValue:
        return self._client.get(f"/brain/model-outputs/governance/{output_governance_id}")

    def segments(self, model_output_id: str, scope: Sequence[str]) -> JSONValue:
        return self._client.get(
            f"/brain/model-outputs/{model_output_id}/segments",
            params={"scope": list(scope)},
        )

    def validate_structured(
        self,
        model_output_id: str,
        scope: Sequence[str],
        *,
        schema_name: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {}
        if schema_name is not None:
            payload["schema_name"] = schema_name
        return self._client.post(
            f"/brain/model-outputs/{model_output_id}/validate-structured",
            json=payload,
            params={"scope": list(scope)},
        )

    def response_candidates(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if trace_id is not None:
            params["trace_id"] = trace_id
        return self._client.get("/brain/model-outputs/response-candidates", params=params)

    def promote_candidate(
        self,
        response_candidate_id: str,
        *,
        actor_id: str | None = None,
        approval_present: bool = False,
        reason: str = "operator_requested",
    ) -> JSONValue:
        payload: JSONDict = {"approval_present": approval_present, "reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/model-outputs/response-candidates/{response_candidate_id}/promote",
            json=payload,
        )

    def tool_intents(
        self,
        scope: Sequence[str],
        *,
        status: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": list(scope), "limit": limit}
        if status is not None:
            params["status"] = status
        if trace_id is not None:
            params["trace_id"] = trace_id
        return self._client.get("/brain/model-outputs/tool-intents", params=params)

    def reject_tool_intent(
        self,
        tool_intent_id: str,
        reason: str,
        actor_id: str | None = None,
    ) -> JSONValue:
        payload: JSONDict = {"reason": reason}
        if actor_id is not None:
            payload["actor_id"] = actor_id
        return self._client.post(
            f"/brain/model-outputs/tool-intents/{tool_intent_id}/reject",
            json=payload,
        )


__all__ = ["ModelOutputsResource"]
