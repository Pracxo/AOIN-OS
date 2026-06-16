"""Learning synthesis query service."""

from __future__ import annotations

from aion_brain.contracts.experience import ExperienceQuery
from aion_brain.contracts.learning_synthesis import ExperienceQueryResult
from aion_brain.learning_synthesis.experience import ExperienceService


class LearningQueryService:
    """Query experience, patterns, lessons, and suggestions through one boundary."""

    def __init__(self, experience_service: ExperienceService) -> None:
        self._experience_service = experience_service

    def query(self, query: ExperienceQuery) -> ExperienceQueryResult:
        """Return learning query results."""
        return self._experience_service.query(query)


__all__ = ["LearningQueryService"]
