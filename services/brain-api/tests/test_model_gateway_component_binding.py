from __future__ import annotations

import pytest

from aion_brain.contracts.secure_runtime import SecureRuntimeGuardOutcome
from tests.model_gateway_aion233_test_support import gateway_setup


def test_component_binding_preserves_current_and_historical_authority() -> None:
    setup = gateway_setup()
    assert setup.binding.current_authorization_transaction_id == "AION-232-SRI-0002"
    assert setup.binding.component_contract_authorization_id == "AION-230-SRI-0001"
    assert setup.binding.component_contract_authorization_closed is True
    assert setup.binding.component_contract_authorization_reactivated is False
    assert setup.parent.capability_plan.capability_code == "brain.think.simulate"
    assert setup.parent.guard_decision.outcome == SecureRuntimeGuardOutcome.allow_simulation
    assert setup.parent.dispatch.status.value == "simulated"
    assert setup.parent.dispatch.actual_execution_performed is False
    assert setup.parent.dispatch.external_call_performed is False
    assert setup.parent.dispatch.production_effect is False


def test_component_binding_rejects_closed_authorization_reactivation() -> None:
    setup = gateway_setup()
    payload = setup.binding.model_dump(mode="python")
    payload["component_contract_authorization_reactivated"] = True
    payload.pop("binding_fingerprint", None)
    with pytest.raises(ValueError):
        type(setup.binding).model_validate(payload)
