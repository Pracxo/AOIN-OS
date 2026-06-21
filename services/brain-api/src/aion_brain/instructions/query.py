"""Read-only instruction query facade."""

from __future__ import annotations

from aion_brain.contracts.instructions import InstructionConflict, InstructionRecord
from aion_brain.contracts.preferences import PreferenceLearningCandidate, PreferenceRecord
from aion_brain.instructions.repository import InstructionRepository


class InstructionQueryService:
    """Read-only query helper used by diagnostics and operator surfaces."""

    def __init__(self, repository: InstructionRepository) -> None:
        self._repository = repository

    def list_instructions(self, scope: list[str], limit: int = 100) -> list[InstructionRecord]:
        return self._repository.list_instructions(scope=scope, limit=limit)

    def list_preferences(self, scope: list[str], limit: int = 100) -> list[PreferenceRecord]:
        return self._repository.list_preferences(scope=scope, limit=limit)

    def list_conflicts(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        severity: str | None = None,
        limit: int = 100,
    ) -> list[InstructionConflict]:
        return self._repository.list_conflicts(
            scope=scope,
            status=status,
            severity=severity,
            limit=limit,
        )

    def list_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PreferenceLearningCandidate]:
        return self._repository.list_candidates(scope=scope, status=status, limit=limit)


__all__ = ["InstructionQueryService"]
