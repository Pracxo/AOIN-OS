"""Entity resolver SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class EntitiesResource:
    """Client helpers for entity registry and resolution APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/entities", json=payload)

    def get(self, entity_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(f"/brain/entities/{entity_id}", params={"scope": scope})

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/entities/query", json=payload)

    def archive(self, entity_id: str, reason: str, scope: list[str]) -> JSONValue:
        return self._client.post(
            f"/brain/entities/{entity_id}/archive",
            params={"scope": scope},
            json={"reason": reason},
        )

    def delete(self, entity_id: str, reason: str, scope: list[str]) -> JSONValue:
        return self._client.delete(
            f"/brain/entities/{entity_id}",
            params={"scope": scope},
            json={"reason": reason},
        )

    def add_alias(self, payload: JSONDict, scope: list[str]) -> JSONValue:
        return self._client.post("/brain/entities/aliases", params={"scope": scope}, json=payload)

    def list_aliases(self, entity_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(f"/brain/entities/{entity_id}/aliases", params={"scope": scope})

    def create_mention(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/entities/mentions", json=payload)

    def list_mentions(self, entity_id: str, scope: list[str], limit: int = 100) -> JSONValue:
        return self._client.get(
            f"/brain/entities/{entity_id}/mentions",
            params={"scope": scope, "limit": limit},
        )

    def extract_mentions(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/entities/extract-mentions", json=payload)

    def resolve(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/entities/resolve", json=payload)

    def get_resolution_run(self, resolution_run_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/entities/resolution-runs/{resolution_run_id}",
            params={"scope": scope},
        )

    def create_reference(self, payload: JSONDict, scope: list[str]) -> JSONValue:
        return self._client.post(
            "/brain/entities/references",
            params={"scope": scope},
            json=payload,
        )

    def list_references(self, scope: list[str], **filters: object) -> JSONValue:
        params: dict[str, object] = {"scope": scope}
        params.update({key: value for key, value in filters.items() if value is not None})
        return self._client.get("/brain/entities/references", params=params)

    def propose_merge(self, payload: JSONDict, scope: list[str]) -> JSONValue:
        return self._client.post(
            "/brain/entities/merge-proposals",
            params={"scope": scope},
            json=payload,
        )

    def approve_merge(
        self,
        proposal_id: str,
        payload: JSONDict | str,
        scope: list[str],
        *,
        approval_present: bool = True,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/entities/merge-proposals/{proposal_id}/approve",
            params={"scope": scope},
            json=_decision_payload(payload, approval_present=approval_present),
        )

    def reject_merge(
        self,
        proposal_id: str,
        payload: JSONDict | str,
        scope: list[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/entities/merge-proposals/{proposal_id}/reject",
            params={"scope": scope},
            json=_decision_payload(payload),
        )

    def propose_split(self, payload: JSONDict, scope: list[str]) -> JSONValue:
        return self._client.post(
            "/brain/entities/split-proposals",
            params={"scope": scope},
            json=payload,
        )

    def approve_split(
        self,
        proposal_id: str,
        payload: JSONDict | str,
        scope: list[str],
        *,
        approval_present: bool = True,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/entities/split-proposals/{proposal_id}/approve",
            params={"scope": scope},
            json=_decision_payload(payload, approval_present=approval_present),
        )

    def reject_split(
        self,
        proposal_id: str,
        payload: JSONDict | str,
        scope: list[str],
    ) -> JSONValue:
        return self._client.post(
            f"/brain/entities/split-proposals/{proposal_id}/reject",
            params={"scope": scope},
            json=_decision_payload(payload),
        )


def _decision_payload(payload: JSONDict | str, *, approval_present: bool = True) -> JSONDict:
    if isinstance(payload, str):
        return {"reason": payload, "approval_present": approval_present}
    return payload
