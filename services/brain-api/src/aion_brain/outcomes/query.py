"""Outcome query service."""

from __future__ import annotations

from aion_brain.contracts.outcomes import OutcomeQuery, OutcomeQueryResult
from aion_brain.outcomes.service import OutcomeService


class OutcomeQueryService:
    """Thin query facade for kernel wiring and future adapters."""

    def __init__(self, outcome_service: OutcomeService) -> None:
        self._outcome_service = outcome_service

    def query(self, query: OutcomeQuery) -> OutcomeQueryResult:
        """Query outcomes."""
        return self._outcome_service.query(query)


__all__ = ["OutcomeQueryService"]
