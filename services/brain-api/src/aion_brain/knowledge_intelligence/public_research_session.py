"""Session-local kill switch for AION-219 public research pilots."""

from __future__ import annotations

from threading import Event, Lock

from aion_brain.contracts.knowledge_public_research_pilot import (
    PublicResearchKillSwitchState,
    reject_prohibited_text,
)


class PublicResearchPilotKilled(RuntimeError):
    """Raised when an operator-triggered kill switch stops a pilot."""

    def __init__(self, stage: str) -> None:
        super().__init__("public_research_pilot_killed")
        self.stage = stage


class PublicResearchPilotKillSwitch:
    """Thread-safe per-session kill switch with no global mutable singleton."""

    def __init__(self) -> None:
        self._event = Event()
        self._lock = Lock()
        self._reason = "armed"

    @property
    def state(self) -> PublicResearchKillSwitchState:
        """Return the current kill-switch state."""

        if self._event.is_set():
            return PublicResearchKillSwitchState.TRIGGERED
        return PublicResearchKillSwitchState.ARMED

    @property
    def reason(self) -> str:
        """Return the redacted local reason."""

        with self._lock:
            return self._reason

    def trigger(self, reason: str = "operator_requested_stop") -> None:
        """Trigger the switch and preserve only a redacted reason code."""

        safe_reason = reject_prohibited_text(reason[:80], "kill switch reason")
        with self._lock:
            self._reason = safe_reason
            self._event.set()

    def raise_if_triggered(self, stage: str) -> None:
        """Fail closed when the switch has been triggered."""

        if self._event.is_set():
            raise PublicResearchPilotKilled(stage)


__all__ = ["PublicResearchPilotKillSwitch", "PublicResearchPilotKilled"]
