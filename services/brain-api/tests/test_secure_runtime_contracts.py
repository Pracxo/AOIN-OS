from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.contracts.secure_runtime import (
    AUTHORIZATION_TRANSACTION_ID,
    CLOSED_CAPABILITY_CODES,
    LOCAL_OPERATOR_CONFIRMATION_TEXT,
    PROGRAM_ID,
    SECURE_RUNTIME_CONTRACT_SCHEMA_VERSION,
    SecureRuntimeDispatchStatus,
    SecureRuntimeGuardOutcome,
    SecureRuntimeMode,
    SecureRuntimeSessionState,
    local_operator_confirmation_fingerprint,
)
from tests.secure_runtime_test_support import secure_runtime_fixture


def test_secure_runtime_contract_constants_match_aion231_authorization() -> None:
    assert SECURE_RUNTIME_CONTRACT_SCHEMA_VERSION == "aion-secure-runtime/v1"
    assert PROGRAM_ID == "AION-SECURE-RUNTIME-INTEGRATION-001"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-230-SRI-0001"
    assert LOCAL_OPERATOR_CONFIRMATION_TEXT == "START_CONTROLLED_LOCAL_OPERATOR_RUNTIME"
    assert len(local_operator_confirmation_fingerprint()) == 64


def test_secure_runtime_enums_do_not_expose_execution_states() -> None:
    values = {
        *[item.value for item in SecureRuntimeMode],
        *[item.value for item in SecureRuntimeSessionState],
        *[item.value for item in SecureRuntimeGuardOutcome],
        *[item.value for item in SecureRuntimeDispatchStatus],
    }
    forbidden = {
        "production_authenticated",
        "external_identity_authenticated",
        "execution_allowed",
        "connector_executed",
        "tool_executed",
        "model_called",
        "module_activated",
        "production_write_applied",
        "production_runtime_active",
    }
    assert values.isdisjoint(forbidden)


def test_every_contract_fingerprint_is_deterministic_and_redacted() -> None:
    fixture = secure_runtime_fixture()
    dumped = fixture.authorization.model_dump(mode="json")
    assert fixture.authorization.envelope_fingerprint
    assert fixture.operator_identity.binding_fingerprint
    assert fixture.dispatch.result_fingerprint
    assert "signature" not in str(dumped).lower()


def test_extra_fields_are_rejected_without_echoing_values() -> None:
    fixture = secure_runtime_fixture()
    payload = fixture.authorization.model_dump(mode="python")
    payload["private_key"] = "do-not-echo"
    with pytest.raises(ValidationError) as exc_info:
        type(fixture.authorization)(**payload)
    assert "do-not-echo" not in str(exc_info.value)


def test_closed_capability_codes_are_exact() -> None:
    assert CLOSED_CAPABILITY_CODES == (
        "brain.think.simulate",
        "secure_runtime.audit.read",
        "secure_runtime.fixture.replay",
        "secure_runtime.health.read",
        "secure_runtime.observability.read",
    )
