"""Release candidate query service."""

from __future__ import annotations

from typing import Any

from aion_brain.contracts.release_candidate import RCQuery
from aion_brain.release_candidate.policy import authorize_rc_action
from aion_brain.release_candidate.repository import ReleaseCandidateRepository


class RCQueryService:
    """Query RC-owned records through one endpoint."""

    def __init__(self, repository: ReleaseCandidateRepository, policy_adapter: object) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter

    def query(self, query: RCQuery) -> dict[str, Any]:
        """Return candidate/run/report/finding summary."""

        authorize_rc_action(self._policy_adapter, "release_candidate.query", query.scope)
        candidates = self._repository.list_candidates(
            status=query.status,
            version=query.version,
            release_ready=query.release_ready,
            limit=query.limit,
        )
        return {
            "candidates": [candidate.model_dump(mode="json") for candidate in candidates],
            "runs": [
                run.model_dump(mode="json") for run in self._repository.list_runs(limit=query.limit)
            ],
            "reports": [
                report.model_dump(mode="json")
                for report in self._repository.list_reports(
                    version=query.version, limit=query.limit
                )
            ],
            "findings": [
                finding.model_dump(mode="json")
                for finding in self._repository.list_findings(status="open", limit=query.limit)
            ],
            "status": self._repository.status(query.scope),
        }


__all__ = ["RCQueryService"]
