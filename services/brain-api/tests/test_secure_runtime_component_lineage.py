from __future__ import annotations

from tests.secure_runtime_test_support import secure_runtime_fixture


def test_component_invocation_bindings_preserve_historical_authority_as_closed() -> None:
    fixture = secure_runtime_fixture()

    bindings = fixture.operator_identity.component_invocation_bindings
    assert {item.component_implementation_task for item in bindings} == {"AION-162", "AION-164"}
    assert all(
        item.current_authorization_transaction_id == "AION-230-SRI-0001" for item in bindings
    )
    assert all(item.component_contract_authorization_closed is True for item in bindings)
    assert all(item.component_contract_authorization_reactivated is False for item in bindings)
    assert all(item.runtime_effect is False for item in bindings)
