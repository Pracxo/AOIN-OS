"""Reasoning adapter interfaces."""

from typing import Protocol

from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket


class ModelGatewayAdapter(Protocol):
    """Interface for future model gateway providers."""

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Complete a provider-neutral prompt packet."""
        ...
