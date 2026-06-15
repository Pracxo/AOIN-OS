"""Placeholder model gateway adapter."""

from aion_brain.contracts.reasoning import ModelCallRecord, ModelRouteDecision, PromptPacket


class PlaceholderModelGatewayAdapter:
    """Adapter boundary for future model gateways such as LiteLLM.

    This is an adapter boundary. AION public contracts must not depend on the
    external framework.
    """

    def complete(self, prompt: PromptPacket, route: ModelRouteDecision) -> ModelCallRecord:
        """Complete through a future model gateway implementation."""
        raise NotImplementedError("Model gateway integration is not implemented in v0.1.")
