from __future__ import annotations

from capability_runtime_test_support import load_runtime
from pydantic import ValidationError


def test_contract_constants_and_closed_state() -> None:
    runtime = load_runtime()
    assert runtime.CAPABILITY_RUNTIME_CONTRACT_SCHEMA_VERSION == "aion-capability-runtime/v1"
    assert runtime.AUTHORIZATION_TRANSACTION_ID == "AION-234-SRI-0003"
    assert runtime.APPROVAL_RECORD_ID == "AION-234-SRI-0003"
    assert runtime.IMPLEMENTATION_TASK == "AION-235"
    assert runtime.FORMAL_CLOSEOUT_TASK == "AION-236"
    assert runtime.LOCAL_CONFIRMATION_TEXT == "RUN_CONTROLLED_SANDBOXED_CAPABILITY_RUNTIME"
    assert runtime.AUTHORIZATION_SCOPE.startswith("authenticated-local-untrusted-model-output")


def test_enums_exclude_external_execution_states() -> None:
    runtime = load_runtime()
    enum_values = {
        item.value
        for enum_type in (
            runtime.CapabilityRuntimeMode,
            runtime.CapabilityExecutionKind,
            runtime.CapabilitySandboxOutcome,
            runtime.CapabilityExecutionStatus,
        )
        for item in enum_type
    }
    forbidden_fragments = {
        "external_execution",
        "live_connector",
        "actual_tool",
        "shell_allowed",
        "process_allowed",
        "filesystem_allowed",
        "network_allowed",
        "production_execution",
    }
    assert enum_values.isdisjoint(forbidden_fragments)


def test_models_forbid_extra_fields_and_redact_validation_input() -> None:
    runtime = load_runtime()
    manifest = runtime.CAPABILITY_MANIFESTS[0].model_dump(mode="json")
    manifest["unexpected"] = "value"
    try:
        runtime.CapabilityManifest(**manifest)
    except ValidationError as exc:
        assert "unexpected" in str(exc)
        assert "value" not in str(exc)
    else:
        raise AssertionError("extra field accepted")
