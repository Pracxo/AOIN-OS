from __future__ import annotations

import json
import os
import subprocess
import tomllib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]

PROGRAM_ID = "AION-ADAPTIVE-INTELLIGENCE-001"
AUTH_ID = "AION-245-AI-0001"
SCOPE = (
    "controlled-provider-neutral-external-cognition-contracts-provider-manifests-model-manifests-"
    "request-response-envelopes-routing-budgets-structured-output-redaction-trust-provenance-"
    "fixture-replay-circuit-breaker-observability-audit-no-network-no-provider-call-no-credential-"
    "value-no-memory-write-no-tool-execution-core"
)
RC1_TAG = "aion-v0.2.0-rc.1"
RC1_TARGET = "d35f1caa234d35dce1dfc0a80bc4c8e327a8373e"
RC1_ASSET_FP = "c228cbe4d3a2ed993d329b1eeb03cddfbc6f6f0f18491bca54a6fd234c32dfcc"
ROADMAP = [f"AION-{number}" for number in range(245, 261)]
APPROVED = {
    "external_cognition_contract_approved",
    "external_cognition_authorization_envelope_approved",
    "existing_model_gateway_component_binding_approved",
    "secure_runtime_component_binding_approved",
    "provider_manifest_approved",
    "model_manifest_approved",
    "model_capability_manifest_approved",
    "model_request_envelope_approved",
    "model_response_envelope_approved",
    "message_normalization_approved",
    "structured_output_schema_approved",
    "structured_output_validation_approved",
    "model_route_policy_approved",
    "capability_based_routing_approved",
    "declared_context_budget_approved",
    "declared_output_budget_approved",
    "declared_cost_budget_approved",
    "latency_budget_approved",
    "retry_policy_approved",
    "circuit_breaker_policy_approved",
    "response_trust_classification_approved",
    "uncertainty_projection_approved",
    "provider_error_normalization_approved",
    "prompt_redaction_policy_approved",
    "response_redaction_policy_approved",
    "prompt_fingerprint_approved",
    "response_fingerprint_approved",
    "deterministic_fixture_provider_approved",
    "deterministic_replay_approved",
    "changed_replay_rejection_approved",
    "audit_evidence_approved",
    "observability_schema_approved",
    "operator_review_record_approved",
    "static_console_evidence_approved",
    "documentation_approved",
}
PROHIBITED = {
    "actual_model_provider_call_enabled",
    "provider_network_adapter_enabled",
    "public_network_access_enabled",
    "external_network_egress_enabled",
    "dns_resolution_enabled",
    "provider_credential_input_enabled",
    "provider_credential_read_enabled",
    "provider_credential_generation_enabled",
    "provider_credential_persistence_enabled",
    "provider_token_input_enabled",
    "provider_token_read_enabled",
    "provider_token_persistence_enabled",
    "provider_authorization_header_creation_enabled",
    "raw_prompt_persistence_enabled",
    "raw_response_persistence_enabled",
    "hidden_reasoning_capture_enabled",
    "model_output_triggered_execution_enabled",
    "model_output_tool_call_enabled",
    "persistent_memory_write_enabled",
    "verified_knowledge_promotion_enabled",
    "actual_belief_mutation_enabled",
    "engagement_learning_enabled",
    "adaptive_routing_runtime_enabled",
    "external_connector_execution_enabled",
    "external_tool_execution_enabled",
    "autonomous_background_loop_enabled",
    "scheduled_provider_calls_enabled",
    "source_rewrite_enabled",
    "runtime_git_mutation_enabled",
    "runtime_pull_request_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "production_runtime_authorized",
    "production_exposure",
}
RESOURCE_LIMITS = {
    "maximum_provider_manifests": 8,
    "maximum_model_manifests": 32,
    "maximum_model_capability_records": 256,
    "maximum_routing_policies": 100,
    "maximum_routing_rules": 500,
    "maximum_request_templates": 100,
    "maximum_structured_output_schemas": 100,
    "maximum_fixture_sessions": 20,
    "maximum_fixture_requests_per_session": 100,
    "maximum_total_fixture_requests": 1000,
    "maximum_messages_per_request": 256,
    "maximum_request_payload_bytes": 2097152,
    "maximum_response_payload_bytes": 4194304,
    "maximum_declared_context_tokens": 2000000,
    "maximum_declared_output_tokens": 262144,
    "maximum_concurrency": 4,
    "maximum_retry_attempts": 3,
    "maximum_circuit_breaker_records": 100,
    "maximum_operator_review_items": 200,
    "maximum_evidence_records": 10000,
    "maximum_evidence_bytes": 104857600,
    "maximum_local_fixture_pilots": 20,
    "maximum_actual_model_provider_calls": 0,
    "maximum_public_network_calls": 0,
    "maximum_external_network_egress_calls": 0,
    "maximum_dns_resolutions": 0,
    "maximum_provider_credentials_generated": 0,
    "maximum_provider_credentials_read": 0,
    "maximum_provider_credentials_persisted": 0,
    "maximum_provider_tokens_read": 0,
    "maximum_provider_tokens_persisted": 0,
    "maximum_authorization_headers_created": 0,
    "maximum_raw_prompts_persisted": 0,
    "maximum_raw_responses_persisted": 0,
    "maximum_hidden_reasoning_records": 0,
    "maximum_memory_writes": 0,
    "maximum_verified_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_external_connector_calls": 0,
    "maximum_external_tool_executions": 0,
    "maximum_background_cycles": 0,
    "maximum_scheduled_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_automatic_merges": 0,
    "maximum_production_deployments": 0,
    "maximum_model_weight_changes": 0,
}
FUTURE_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/external_cognition.py",
    "services/brain-api/src/aion_brain/external_cognition/__init__.py",
    "services/brain-api/src/aion_brain/external_cognition/authorization.py",
    "services/brain-api/src/aion_brain/external_cognition/component_binding.py",
    "services/brain-api/src/aion_brain/external_cognition/provider_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/model_manifest.py",
    "services/brain-api/src/aion_brain/external_cognition/request_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/response_envelope.py",
    "services/brain-api/src/aion_brain/external_cognition/message_normalization.py",
    "services/brain-api/src/aion_brain/external_cognition/structured_output.py",
    "services/brain-api/src/aion_brain/external_cognition/routing_policy.py",
    "services/brain-api/src/aion_brain/external_cognition/budgets.py",
    "services/brain-api/src/aion_brain/external_cognition/trust.py",
    "services/brain-api/src/aion_brain/external_cognition/redaction.py",
    "services/brain-api/src/aion_brain/external_cognition/circuit_breaker.py",
    "services/brain-api/src/aion_brain/external_cognition/fixture_provider.py",
    "services/brain-api/src/aion_brain/external_cognition/replay.py",
    "services/brain-api/src/aion_brain/external_cognition/observability.py",
    "services/brain-api/src/aion_brain/external_cognition/audit.py",
    "services/brain-api/src/aion_brain/external_cognition/integrity.py",
    "services/brain-api/src/aion_brain/external_cognition/evidence.py",
    "scripts/external-cognition-fixture-local-run.py",
}


def load_json(relative: str) -> dict:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def read_text(relative: str) -> str:
    return (REPO_ROOT / relative).read_text(encoding="utf-8")


def project_version(relative: str) -> str:
    with (REPO_ROOT / relative).open("rb") as handle:
        return tomllib.load(handle)["project"]["version"]


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=REPO_ROOT, capture_output=True, text=True, check=check)


def test_aion244_publication_reconciliation_and_rc1_evidence_are_intact() -> None:
    publication = load_json("examples/v02-release-qualification/v02-rc1-publication-evidence.json")

    assert publication["tag_name"] == RC1_TAG
    assert publication["tag_target_commit"] == RC1_TARGET
    assert publication["release_name"] == "AION OS v0.2.0-rc.1"
    assert publication["release_asset_count"] == 24
    assert publication["assets_uploaded"] == 24
    assert publication["assets_downloaded_for_verification"] == 24
    assert publication["asset_hash_matches"] == 24
    assert publication["asset_hash_failures"] == 0
    assert publication["asset_inventory_fingerprint"] == RC1_ASSET_FP
    assert publication["stable_tags_created"] == 0
    assert publication["stable_releases_created"] == 0
    assert publication["production_deployments"] == 0

    program = load_json("docs/v02-release-qualification/program-ledger.json")
    assert program["v02_release_qualification_program_complete"] is True
    assert program["active_v02_release_qualification_authorization_count"] == 0


def test_rc1_tag_integrity_when_tag_is_available_and_stable_v02_absent() -> None:
    tag_type = run(["git", "cat-file", "-t", RC1_TAG], check=False)
    if tag_type.returncode == 0:
        assert tag_type.stdout.strip() == "tag"
        target = run(["git", "rev-parse", f"{RC1_TAG}^{{}}"]).stdout.strip()
        assert target == RC1_TARGET
        tagged_brain = run(["git", "show", f"{RC1_TAG}:services/brain-api/pyproject.toml"]).stdout
        tagged_sdk = run(
            ["git", "show", f"{RC1_TAG}:packages/aion-sdk-python/pyproject.toml"]
        ).stdout
        assert 'version = "0.2.0rc1"' in tagged_brain
        assert 'version = "0.2.0rc1"' in tagged_sdk

    assert run(["git", "tag", "--list", "aion-v0.2.0", "v0.2.0*"]).stdout.strip() == ""


def test_post_rc1_development_versions_are_v030_dev0() -> None:
    assert project_version("services/brain-api/pyproject.toml") == "0.3.0.dev0"
    assert project_version("packages/aion-sdk-python/pyproject.toml") == "0.3.0.dev0"


def test_program_charter_parent_lineage_and_roadmap_are_exact() -> None:
    program = load_json("docs/adaptive-intelligence/program-ledger.json")

    assert program["program_id"] == PROGRAM_ID
    assert program["program_name"] == "AION Adaptive Intelligence Programme"
    assert (
        program["program_state"]
        == "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
    )
    assert program["adaptive_intelligence_program_implemented"] is False
    assert program["external_cognition_gateway_implemented"] is True
    assert (
        program["external_cognition_gateway_state"]
        == "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout"
    )
    assert program["parent_program_id"] == "AION-V02-RELEASE-QUALIFICATION-001"
    assert program["parent_final_task"] == "AION-244"
    assert program["parent_final_main_commit"] == "2a5db0760178698d783abcc63e53f08ff3583571"
    assert program["parent_final_evaluation_id"] == "AION-V02RQPE-003"
    assert program["parent_final_evaluation_fingerprint"] == (
        "8bb225c4f8e5055bc19d961e9a67e7347acf0896195ce4279ba65d597c044952"
    )
    assert program["parent_release_tag"] == RC1_TAG
    assert program["parent_release_tag_target"] == RC1_TARGET
    assert program["parent_release_asset_count"] == 24
    assert program["parent_release_asset_inventory_fingerprint"] == RC1_ASSET_FP
    assert [item["task_id"] for item in program["roadmap"]] == ROADMAP
    assert (
        program["roadmap"][1]["state"]
        == "implemented_fixture_pilot_complete_pending_AION-247_closeout"
    )
    assert (
        program["roadmap"][2]["state"]
        == "active_foundation_evaluation_and_live_provider_pilot_authorization_decision"
    )
    assert {item["state"] for item in program["roadmap"][3:]} == {"planned_unauthorized"}


def test_authorization_lifecycle_and_scope_authorize_aion246_only() -> None:
    ledger = load_json("docs/adaptive-intelligence/authorization-ledger.json")
    record = ledger["records"][0]

    assert ledger["active_adaptive_intelligence_authorization_count"] == 1
    assert ledger["active_adaptive_intelligence_authorization"] == AUTH_ID
    assert ledger["active_adaptive_intelligence_task"] == "AION-246"
    assert record["authorization_transaction_id"] == AUTH_ID
    assert record["approval_record_id"] == AUTH_ID
    assert record["implementation_task"] == "AION-246"
    assert record["formal_closeout_task"] == "AION-247"
    assert record["final_planned_task"] == "AION-260"
    assert record["authorization_scope"] == SCOPE
    assert record["authorization_active"] is True
    assert record["authorization_consumed"] is False
    assert record["authorization_expired"] is False
    assert record["authorization_reusable"] is False


def test_approved_capabilities_prohibited_capabilities_and_resource_limits_are_exact() -> None:
    program = load_json("docs/adaptive-intelligence/program-ledger.json")
    record = load_json("docs/adaptive-intelligence/authorization-ledger.json")["records"][0]

    assert set(program["approved_capabilities"]) == APPROVED
    assert set(record["approved_capabilities"]) == APPROVED
    assert all(program["approved_capabilities"][key] is True for key in APPROVED)
    assert all(record["approved_capabilities"][key] is True for key in APPROVED)

    assert set(program["prohibited_capabilities"]) == PROHIBITED
    assert set(record["prohibited_capabilities"]) == PROHIBITED
    assert all(program["prohibited_capabilities"][key] is False for key in PROHIBITED)
    assert all(record["prohibited_capabilities"][key] is False for key in PROHIBITED)

    assert program["resource_limits"] == RESOURCE_LIMITS


def test_current_status_blocks_are_reconciled() -> None:
    required_files = [
        "README.md",
        "AGENTS.md",
        "docs/project-status.md",
        "docs/architecture.md",
        "docs/brain-contract.md",
        "docs/visual-brain.md",
        "docs/v02-release-qualification/architecture-roadmap.md",
        "operator-console-static/README.md",
    ]
    required_terms = [
        "aion-v0.2.0-rc.1",
        "v0.3",
        "0.3.0.dev0",
        PROGRAM_ID,
        "AION-246",
        AUTH_ID,
    ]

    for relative in required_files:
        text = read_text(relative)
        for term in required_terms:
            assert term in text, f"{term} missing from {relative}"

    project_status = read_text("docs/project-status.md")
    assert "pending PR merge, RC1 prerelease publication" not in project_status
    assert "Current task: AION-243" not in project_status


def test_aion246_source_is_disabled_and_no_provider_runtime_effects_exist() -> None:
    for relative in FUTURE_SOURCE:
        assert (REPO_ROOT / relative).exists(), relative

    for relative in (
        "services/brain-api/src/aion_brain/external_cognition/network.py",
        "services/brain-api/src/aion_brain/external_cognition/http_client.py",
        "services/brain-api/src/aion_brain/external_cognition/openai.py",
        "services/brain-api/src/aion_brain/external_cognition/anthropic.py",
        "services/brain-api/src/aion_brain/external_cognition/google.py",
        "services/brain-api/src/aion_brain/external_cognition/azure_openai.py",
        "services/brain-api/src/aion_brain/external_cognition/credential_store.py",
        "services/brain-api/src/aion_brain/external_cognition/token_store.py",
        "services/brain-api/src/aion_brain/external_cognition/background_worker.py",
        "services/brain-api/src/aion_brain/external_cognition/scheduler.py",
        "services/brain-api/src/aion_brain/api/external_cognition.py",
    ):
        assert not (REPO_ROOT / relative).exists(), relative

    hold = load_json("examples/adaptive-intelligence/runtime-hold.json")
    for key in (
        "actual_provider_calls",
        "public_network_calls",
        "dns_resolutions",
        "provider_credentials_read",
        "provider_tokens_read",
        "persistent_memory_writes",
        "external_tool_executions",
        "external_connector_calls",
        "autonomous_background_cycles",
        "production_deployments",
    ):
        assert hold[key] == 0


def test_static_console_evidence_and_validation_scripts_are_present_and_safe() -> None:
    for relative in (
        "operator-console-static/demo-data/adaptive-intelligence-program.json",
        "operator-console-static/demo-data/external-cognition-authorization.json",
        "operator-console-static/demo-data/adaptive-intelligence-runtime-hold.json",
    ):
        payload = load_json(relative)
        assert payload["read_only"] is True
        assert payload["runtime_effect"] is False

    for relative in (
        "scripts/post-rc1-development-baseline-check.sh",
        "scripts/adaptive-intelligence-program-authorization-check.sh",
        "scripts/adaptive-intelligence-program-authorization-no-go-regression.sh",
        "scripts/adaptive-intelligence-runtime-hold.sh",
    ):
        path = REPO_ROOT / relative
        assert path.is_file()
        assert os.access(path, os.X_OK)


def test_focused_validation_scripts_pass_without_nested_full_check() -> None:
    env = {
        **os.environ,
        "AION_ADAPTIVE_INTELLIGENCE_RUNTIME_HOLD_SKIP_FULL_CHECK": "1",
    }
    for script in (
        "./scripts/adaptive-intelligence-program-authorization-check.sh",
        "./scripts/adaptive-intelligence-program-authorization-no-go-regression.sh",
        "./scripts/adaptive-intelligence-runtime-hold.sh",
    ):
        result = subprocess.run(
            [script],
            cwd=REPO_ROOT,
            env=env,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "PASS" in result.stdout
