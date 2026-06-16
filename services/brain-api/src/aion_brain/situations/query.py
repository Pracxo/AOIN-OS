"""Read-side situation query service."""

from __future__ import annotations

from aion_brain.contracts.situations import SituationQuery, SituationQueryResult
from aion_brain.situations.service import SituationService


class SituationQueryService:
    """Small facade for situation and atom queries."""

    def __init__(self, situation_service: SituationService) -> None:
        self._situation_service = situation_service

    def query(self, query: SituationQuery) -> SituationQueryResult:
        return self._situation_service.query(query)
