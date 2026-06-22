"""Replay boundary for event reaction dead letters."""

from aion_brain.contracts.event_reactions import EventDispatchRecord
from aion_brain.event_reactions.dead_letters import EventDeadLetterService


class EventReactionReplayService:
    """Thin replay service around dead-letter replay rules."""

    def __init__(self, dead_letter_service: EventDeadLetterService) -> None:
        self._dead_letter_service = dead_letter_service

    def replay_dead_letter(
        self,
        dead_letter_id: str,
        *,
        approval_present: bool = False,
    ) -> EventDispatchRecord:
        """Replay a dead-lettered reaction through the router."""
        return self._dead_letter_service.replay(
            dead_letter_id,
            approval_present=approval_present,
        )
