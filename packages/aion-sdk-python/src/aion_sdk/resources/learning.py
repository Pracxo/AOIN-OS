"""Experience ledger and learning synthesis SDK resource."""

from __future__ import annotations

from typing import TYPE_CHECKING

from aion_sdk.types import JSONDict, JSONValue

if TYPE_CHECKING:
    from aion_sdk.client import AIONClient


class LearningResource:
    """Client helpers for learning synthesis APIs."""

    def __init__(self, client: AIONClient) -> None:
        self._client = client

    def create_experience(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/learning/experiences", json=payload)

    def get_experience(self, experience_id: str, scope: list[str]) -> JSONValue:
        return self._client.get(
            f"/brain/learning/experiences/{experience_id}",
            params={"scope": scope},
        )

    def query(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/learning/query", json=payload)

    def archive_experience(self, experience_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/learning/experiences/{experience_id}/archive",
            json={"reason": reason},
        )

    def mine_patterns(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/learning/patterns/mine", json=payload)

    def list_patterns(
        self,
        *,
        scope: list[str],
        pattern_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if pattern_type:
            params["pattern_type"] = pattern_type
        if status:
            params["status"] = status
        return self._client.get("/brain/learning/patterns", params=params)

    def list_lessons(
        self,
        *,
        scope: list[str],
        lesson_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if lesson_type:
            params["lesson_type"] = lesson_type
        if status:
            params["status"] = status
        return self._client.get("/brain/learning/lessons", params=params)

    def synthesize(self, payload: JSONDict) -> JSONValue:
        return self._client.post("/brain/learning/synthesize", json=payload)

    def get_synthesis(self, synthesis_run_id: str) -> JSONValue:
        return self._client.get(f"/brain/learning/synthesis/{synthesis_run_id}")

    def list_skill_suggestions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status:
            params["status"] = status
        return self._client.get("/brain/learning/skill-suggestions", params=params)

    def accept_skill_suggestion(self, suggestion_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/learning/skill-suggestions/{suggestion_id}/accept",
            json={"reason": reason},
        )

    def reject_skill_suggestion(self, suggestion_id: str, reason: str) -> JSONValue:
        return self._client.post(
            f"/brain/learning/skill-suggestions/{suggestion_id}/reject",
            json={"reason": reason},
        )

    def convert_skill_suggestion(
        self,
        suggestion_id: str,
        *,
        reason: str,
        approval_present: bool = False,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/learning/skill-suggestions/{suggestion_id}/convert-to-candidate",
            json={"reason": reason, "approval_present": approval_present},
        )

    def list_regression_suggestions(
        self,
        *,
        scope: list[str],
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> JSONValue:
        params: dict[str, object] = {"scope": scope, "limit": limit}
        if status:
            params["status"] = status
        if severity:
            params["severity"] = severity
        return self._client.get("/brain/learning/regression-suggestions", params=params)

    def accept_regression_suggestion(
        self,
        regression_suggestion_id: str,
        reason: str,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/learning/regression-suggestions/{regression_suggestion_id}/accept",
            json={"reason": reason},
        )

    def reject_regression_suggestion(
        self,
        regression_suggestion_id: str,
        reason: str,
    ) -> JSONValue:
        return self._client.post(
            f"/brain/learning/regression-suggestions/{regression_suggestion_id}/reject",
            json={"reason": reason},
        )


__all__ = ["LearningResource"]
