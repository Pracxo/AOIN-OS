from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.knowledge_tool_verification import (
    AUTHORIZATION_TRANSACTION_ID,
    MAXIMUM_ACTUAL_TOOL_EXECUTIONS,
    MAXIMUM_PERSISTENT_TOOL_STATE_WRITE_BATCH,
    TOOL_VERIFICATION_CONTRACT_SCHEMA_VERSION,
    TOOL_VERIFICATION_FABRIC_STATE,
    ToolEffectType,
    ToolOperationClass,
    ToolRiskClass,
    ToolSessionOutcome,
    ToolVerificationResourceBudget,
    VerifierRole,
)
from aion_brain.knowledge_intelligence.tool_attestation import attestation_chain_is_valid
from aion_brain.knowledge_intelligence.tool_manifests import (
    InMemoryToolManifestRegistry,
    build_default_tool_manifest_registry,
    build_permission_envelope,
    build_schema_descriptor,
    build_tool_manifest,
)
from aion_brain.knowledge_intelligence.tool_planning import (
    build_tool_intent,
    build_tool_plan,
    enumerate_eligible_tool_candidates,
)
from aion_brain.knowledge_intelligence.tool_simulation import (
    build_tool_fixture_envelope,
)
from aion_brain.knowledge_intelligence.tool_verification import (
    validate_payload_against_schema,
)
from aion_brain.knowledge_intelligence.tool_verification_fabric import (
    ControlledToolVerificationFabric,
)

REPO_ROOT = Path(__file__).resolve().parents[3]
SOURCE_FILES = (
    "services/brain-api/src/aion_brain/contracts/knowledge_tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification_fabric.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_manifests.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_planning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_simulation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_attestation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_effects.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_evidence.py",
)


def test_tool_verification_contract_preserves_authorization_and_zero_runtime_budget() -> None:
    assert TOOL_VERIFICATION_CONTRACT_SCHEMA_VERSION == "aion-knowledge-tool-verification/v1"
    assert AUTHORIZATION_TRANSACTION_ID == "AION-214-KI-0006"
    assert TOOL_VERIFICATION_FABRIC_STATE == (
        "implemented_deterministic_simulation_verification_attestation_persistent_write_disabled"
    )
    assert MAXIMUM_PERSISTENT_TOOL_STATE_WRITE_BATCH == 0
    assert MAXIMUM_ACTUAL_TOOL_EXECUTIONS == 0

    budget = ToolVerificationResourceBudget()
    assert budget.maximum_persistent_tool_state_write_batch == 0
    assert budget.maximum_actual_tool_executions == 0
    assert budget.maximum_shell_commands == 0
    assert budget.maximum_network_calls == 0
    assert budget.maximum_model_provider_calls == 0

    with pytest.raises(ValidationError):
        ToolVerificationResourceBudget(unexpected=True)


def test_manifest_registry_is_versioned_in_memory_and_deterministic() -> None:
    first = build_default_tool_manifest_registry().snapshot()
    second = build_default_tool_manifest_registry().snapshot()

    assert first.registry_fingerprint == second.registry_fingerprint
    assert first.in_memory_only is True
    assert first.persistent_write_applied is False
    assert [manifest.manifest_id for manifest in first.manifests] == sorted(
        manifest.manifest_id for manifest in first.manifests
    )
    for manifest in first.manifests:
        assert manifest.synthetic is True
        assert manifest.actual_execution_enabled is False
        assert manifest.actual_tool_executed is False
        assert manifest.persistent_write_applied is False
        assert manifest.runtime_effect is False


def test_intent_candidate_selection_and_plan_are_exact_and_deterministic() -> None:
    registry = build_default_tool_manifest_registry().snapshot()
    intent = build_tool_intent(
        requested_tool_ids=("synthetic.json-validator",),
        required_operation_classes=(ToolOperationClass.DETERMINISTIC_VALIDATOR,),
    )

    candidates = enumerate_eligible_tool_candidates(intent, registry)
    plan = build_tool_plan(intent=intent, registry=registry)

    assert [candidate.tool_id for candidate in candidates] == ["synthetic.json-validator"]
    assert plan.selected_candidate_id == candidates[0].candidate_id
    assert plan.steps[0].tool_id == "synthetic.json-validator"
    assert plan.steps[0].simulation_only is True
    assert plan.steps[0].actual_execution_enabled is False
    assert plan.steps[0].persistent_write_applied is False
    assert (
        plan.plan_fingerprint == build_tool_plan(intent=intent, registry=registry).plan_fingerprint
    )


def test_schema_validation_and_simulation_outputs_are_canonical_and_fingerprinted() -> None:
    registry = build_default_tool_manifest_registry().snapshot()
    fabric = ControlledToolVerificationFabric()
    session = fabric.run_session()
    manifest = next(
        item for item in registry.manifests if item.manifest_id == session.plan.steps[0].manifest_id
    )

    assert session.overall_status == ToolSessionOutcome.SIMULATION_PASSED
    assert session.simulation.status.value == "simulation_passed"
    assert session.simulation.actual_tool_executed is False
    assert session.simulation.persistent_write_applied is False
    assert (
        session.simulation.output_fingerprint == session.simulation.artifacts[0].output_fingerprint
    )
    assert validate_payload_against_schema(
        session.plan.steps[0].input_payload, manifest.input_schema
    ) == (
        True,
        ("tool_schema_valid",),
    )
    assert validate_payload_against_schema(
        session.simulation.canonical_output,
        manifest.output_schema,
    ) == (True, ("tool_schema_valid",))


def test_high_risk_plan_requires_safety_rollback_and_resource_verifiers() -> None:
    input_schema = build_schema_descriptor(
        schema_id="schema-elevated-input",
        required_fields=("artifact_kind", "content_fingerprint"),
        optional_fields=("case_id",),
        field_types={"artifact_kind": "str", "content_fingerprint": "str", "case_id": "str"},
    )
    output_schema = build_schema_descriptor(
        schema_id="schema-elevated-output",
        required_fields=("status", "input_fingerprint", "tool_id", "validated"),
        optional_fields=("plan_id",),
        field_types={
            "status": "str",
            "input_fingerprint": "str",
            "tool_id": "str",
            "validated": "bool",
            "plan_id": "str",
        },
    )
    manifest = build_tool_manifest(
        manifest_id="manifest-elevated-validator",
        tool_id="synthetic.elevated-validator",
        tool_version="1.0.0",
        operation_class=ToolOperationClass.DETERMINISTIC_VALIDATOR,
        risk_class=ToolRiskClass.HIGH,
        input_schema=input_schema,
        output_schema=output_schema,
        permission_envelope=build_permission_envelope(),
        declared_effect_type=ToolEffectType.VALIDATE,
        declared_effect_scope="synthetic-artifact",
    )
    registry = InMemoryToolManifestRegistry(manifests=(manifest,)).snapshot()
    intent = build_tool_intent(max_risk_class=ToolRiskClass.HIGH)
    plan = build_tool_plan(intent=intent, registry=registry)

    assert {
        VerifierRole.SAFETY,
        VerifierRole.ROLLBACK,
        VerifierRole.RESOURCE,
    }.issubset(set(plan.required_verifier_roles))


def test_fixture_replay_is_read_only_and_rejects_repository_paths(tmp_path: Path) -> None:
    fabric = ControlledToolVerificationFabric(repository_root=REPO_ROOT)
    registry = build_default_tool_manifest_registry().snapshot()
    fixture = build_tool_fixture_envelope(
        registry_snapshot=registry,
        fixture_records=({"record_id": "fixture-record-001", "redacted": True},),
    )
    fixture_path = tmp_path / "tool-fixture.json"
    fixture_path.write_text(fixture.model_dump_json(indent=2), encoding="utf-8")

    session = fabric.replay_fixture(fixture_path)

    assert session.overall_status == ToolSessionOutcome.SIMULATION_PASSED
    assert session.resource_usage.fixture_records == 1
    assert session.actual_tool_executed is False
    assert session.persistent_write_applied is False
    assert fabric.reject_persistent_write({"attempt": "persist"}) == (
        ToolSessionOutcome.PERSISTENT_WRITE_DISABLED
    )
    with pytest.raises(ValueError):
        fabric.replay_fixture(
            REPO_ROOT / "examples/knowledge-intelligence/tool-verification-session.json"
        )


def test_attestation_chain_and_integrity_report_detect_tampering() -> None:
    fabric = ControlledToolVerificationFabric()
    session = fabric.run_session()
    report = fabric.audit_last_session()

    assert attestation_chain_is_valid(session.attestations) is True
    assert report.status.value == "pass"
    tampered = session.attestations[1].model_copy(
        update={"previous_attestation_fingerprint": "0" * 64}
    )
    assert attestation_chain_is_valid((session.attestations[0], tampered)) is False


def test_tool_verification_source_has_no_runtime_adapter_or_registration() -> None:
    forbidden_tokens = (
        "import requests",
        "import httpx",
        "import socket",
        "import subprocess",
        "create_engine(",
        "APIRouter(",
        "FastAPI(",
        "click.command",
        "typer.Typer",
        "scheduler",
        "background worker",
    )
    for relative in SOURCE_FILES:
        text = (REPO_ROOT / relative).read_text(encoding="utf-8")
        for token in forbidden_tokens:
            assert token not in text, (relative, token)
