"""Runtime adapter interfaces."""

from typing import Protocol

from aion_brain.contracts.events import AIONEvent
from aion_brain.contracts.traces import DecisionTrace


class BrainRuntimeAdapter(Protocol):
    """Interface for future Brain runtime engines."""

    def run(self, event: AIONEvent) -> DecisionTrace:
        """Run the runtime against an event and return a public trace."""
        ...
