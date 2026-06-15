"""Policy adapter interfaces."""

from typing import Protocol

from aion_brain.contracts.policy import PolicyDecision, PolicyRequest


class PolicyAdapter(Protocol):
    """Interface for future policy engines."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        """Authorize an action or plan."""
        ...
