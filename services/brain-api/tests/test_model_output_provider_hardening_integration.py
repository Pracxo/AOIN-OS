"""Model output governance integration for provider simulations."""

from __future__ import annotations

from aion_brain.model_outputs.governance import OutputGovernanceService


def test_model_output_governance_exposes_provider_simulation_requirements() -> None:
    service = OutputGovernanceService(repository=object(), policy_adapter=None)

    requirements = service.provider_simulation_requirements()

    assert requirements["output_governance_required"] is True
    assert requirements["raw_output_storage_allowed"] is False
