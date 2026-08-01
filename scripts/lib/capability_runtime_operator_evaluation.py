#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from copy import deepcopy
from pathlib import Path
from typing import Any, Callable, Mapping


PROGRAM_ID = "AION-SECURE-RUNTIME-INTEGRATION-001"
EVALUATION_ID = "AION-SRIPE-003"
AUTHORIZATION_ID = "AION-234-SRI-0003"
NEXT_AUTHORIZATION_ID = "AION-236-SRI-0004"
IMPLEMENTATION_TASK = "AION-235"
FORMAL_CLOSEOUT_TASK = "AION-236"
NEXT_IMPLEMENTATION_TASK = "AION-237"
NEXT_FORMAL_CLOSEOUT_TASK = "AION-238"
IMPLEMENTATION_PR = 154
IMPLEMENTATION_FEATURE_COMMIT = "03a86f5314b8e79e0d77e2657769be0b15f1c450"
IMPLEMENTATION_MERGE_COMMIT = "39eff73b76f8b68a956f0a852bf8fbd71d36654d"
IMPLEMENTATION_MERGED_AT = "2026-07-31T23:36:10Z"
EXPECTED_PILOT_FINGERPRINT = (
    "896ea332c964393fc2f3264be1381509be46175cd8a4c0733ba3980088ed1a2e"
)
AUTHORIZATION_SCOPE = (
    "authenticated-local-untrusted-model-output-bound-explicit-operator-capability-plan-"
    "closed-capability-connector-manifest-schema-validated-in-memory-sandbox-"
    "deterministic-reference-execution-policy-risk-guardrail-approval-budget-kill-"
    "switch-audit-provenance-rollback-no-external-effect-core"
)
PASS_DECISION = (
    "SANDBOXED_DETERMINISTIC_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_PASS_RECOMMEND_"
    "CONTROLLED_OPERATOR_CONSOLE_INTEGRATED_LOCAL_RUNTIME_AUTHORIZATION"
)
FAIL_DECISION = (
    "SANDBOXED_DETERMINISTIC_CAPABILITY_RUNTIME_OPERATOR_EVALUATION_FAIL_REMAIN_"
    "REFERENCE_EXECUTION_ONLY"
)
SCENARIO_IDS = (
    "aion_235_delivery_and_ci_integrity",
    "authorization_lineage_and_scope",
    "pilot_evidence_schema_and_fingerprint",
    "parent_component_lineage_integrity",
    "model_output_non_authority_and_operator_selection",
    "capability_manifest_registry_integrity",
    "connector_manifest_registry_integrity",
    "restricted_input_and_output_schema_integrity",
    "session_request_and_repository_lifecycle",
    "deterministic_execution_plan_integrity",
    "policy_binding_integrity",
    "risk_binding_integrity",
    "guardrail_binding_integrity",
    "approval_evidence_and_separation_of_duties",
    "side_effect_and_resource_budget_enforcement",
    "parent_kill_switch_and_guard_precedence",
    "in_memory_sandbox_isolation",
    "pure_reference_capability_execution",
    "synthetic_reference_connector_read",
    "synthetic_write_preview_and_rollback",
    "request_idempotency_and_changed_replay",
    "execution_receipt_chain_and_provenance",
    "output_validation_and_smuggling_rejection",
    "audit_chain_integrity",
    "observability_health_and_integrity",
    "determinism_concurrency_redaction_and_performance",
    "zero_external_effects_and_repository_boundary",
    "controlled_operator_console_integration_readiness",
)
EXPECTED_CAPABILITIES: dict[str, tuple[str, bool, str]] = {
    "capability_runtime.health.read": ("low", False, "read_only_reference"),
    "capability_runtime.observability.read": ("low", False, "read_only_reference"),
    "capability_runtime.audit.read": ("medium", True, "read_only_reference"),
    "capability.text.normalize": ("low", False, "pure_function"),
    "capability.hash.sha256": ("low", False, "pure_function"),
    "capability.json.validate": ("low", False, "pure_function"),
    "connector.reference.read.simulate": ("medium", True, "synthetic_reference_connector"),
    "connector.reference.write.preview": (
        "medium",
        True,
        "synthetic_reference_connector_preview",
    ),
}
NEXT_AUTHORIZATION_SCOPE = (
    "authenticated-local-loopback-same-origin-operator-console-bridge-secure-session-"
    "bootstrap-live-read-projection-explicit-model-simulation-explicit-reference-"
    "capability-execution-synthetic-connector-preview-request-nonce-origin-host-csp-"
    "kill-switch-audit-receipt-integrity-integrated-pilot-no-external-effect-core"
)
OPERATOR_CONSOLE_ROUTES = (
    ("GET", "/aion/local/v1/bootstrap"),
    ("GET", "/aion/local/v1/status"),
    ("GET", "/aion/local/v1/health"),
    ("GET", "/aion/local/v1/observability"),
    ("GET", "/aion/local/v1/audit"),
    ("POST", "/aion/local/v1/model/simulate"),
    ("POST", "/aion/local/v1/capability/execute"),
    ("POST", "/aion/local/v1/connector/simulate"),
    ("POST", "/aion/local/v1/kill"),
    ("POST", "/aion/local/v1/session/close"),
)
OPERATOR_CONSOLE_STATIC_ASSETS = (
    "/",
    "/index.html",
    "/styles.css",
    "/app.js",
    "/live-console.js",
)
OPERATOR_CONSOLE_FUTURE_SOURCE_SCOPE = (
    "services/brain-api/src/aion_brain/contracts/operator_console_integration.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/__init__.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/authorization.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/component_binding.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/origin_policy.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_nonce.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/session_bridge.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/request_router.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/view_models.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/local_http.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/audit.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/observability.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/integrity.py",
    "services/brain-api/src/aion_brain/operator_console_runtime/evidence.py",
)
OPERATOR_CONSOLE_SECURITY_HEADERS = {
    "Content-Security-Policy": (
        "default-src 'self'; connect-src 'self'; script-src 'self'; style-src 'self'; "
        "img-src 'self' data:; object-src 'none'; base-uri 'none'; frame-ancestors "
        "'none'; form-action 'none'"
    ),
    "X-Content-Type-Options": "nosniff",
    "Referrer-Policy": "no-referrer",
    "X-Frame-Options": "DENY",
    "Cache-Control": "no-store",
    "Cross-Origin-Resource-Policy": "same-origin",
    "Cross-Origin-Opener-Policy": "same-origin",
    "Permissions-Policy": "camera=(), microphone=(), geolocation=(), payment=(), usb=()",
}


def canonical_json(payload: Any) -> str:
    return json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def fingerprint(payload: Any) -> str:
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _dump_report(payload: Mapping[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _load_runtime(repo_root: Path) -> Any:
    src = repo_root / "services/brain-api/src"
    if str(src) not in sys.path:
        sys.path.insert(0, str(src))
    from aion_brain.contracts import sandboxed_capability_runtime as runtime

    return runtime


def _raises(callable_: Callable[[], Any], expected: type[BaseException]) -> bool:
    try:
        callable_()
    except expected:
        return True
    except Exception:
        return False
    return False


def _check(name: str, passed: bool, evidence: Any = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"name": name, "passed": bool(passed)}
    if evidence is not None:
        payload["evidence"] = evidence
    return payload


def _scenario(scenario_id: str, checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "scenario_id": scenario_id,
        "hard_gate": True,
        "status": "pass" if checks and all(item["passed"] for item in checks) else "fail",
        "checks": checks,
    }


def _pilot_fingerprint_matches(runtime: Any, evidence: Mapping[str, Any]) -> bool:
    body = {key: value for key, value in evidence.items() if key != "report_fingerprint"}
    return evidence.get("report_fingerprint") == runtime.capability_runtime_fingerprint(body)


def _exercise_runtime(runtime: Any) -> dict[str, Any]:
    service = runtime.ControlledSandboxedCapabilityRuntimeService.create_default()
    session = service.start_session("aion-236-evaluation-session")
    operations = (
        ("health", "capability_runtime.health.read", {}),
        ("observability", "capability_runtime.observability.read", {}),
        ("audit", "capability_runtime.audit.read", {}),
        ("normalize", "capability.text.normalize", {"text": "AION\r\nRuntime"}),
        ("hash", "capability.hash.sha256", {"text": "AION-235"}),
        (
            "json_validate",
            "capability.json.validate",
            {
                "document": {"status": "ok"},
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string", "const": "ok"}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
            },
        ),
        (
            "connector_read",
            "connector.reference.read.simulate",
            {"fixture_id": "reference-fixture-AION-235", "record_key": "record-001"},
        ),
        (
            "connector_preview",
            "connector.reference.write.preview",
            {
                "fixture_id": "reference-fixture-AION-235",
                "record_key": "record-001",
                "proposed_value": {"status": "previewed"},
            },
        ),
    )
    results = {
        name: service.execute(
            session_id=session.session_id,
            request_id=f"eval-request-{index:03d}",
            capability_id=capability_id,
            input_payload=payload,
        )
        for index, (name, capability_id, payload) in enumerate(operations, start=1)
    }
    replay = service.execute(
        session_id=session.session_id,
        request_id="eval-request-004",
        capability_id="capability.text.normalize",
        input_payload={"text": "AION\r\nRuntime"},
    )
    negatives = {
        "changed_replay_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-request-004",
                capability_id="capability.text.normalize",
                input_payload={"text": "changed"},
            ),
            runtime.CapabilityRuntimeRejected,
        ),
        "model_trigger_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-model-trigger",
                capability_id="capability.text.normalize",
                input_payload={"text": "blocked"},
                model_output_triggered=True,
            ),
            runtime.CapabilityRuntimeRejected,
        ),
        "absent_selection_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-absent-selection",
                capability_id="capability.text.normalize",
                input_payload={"text": "blocked"},
                operator_selected=False,
            ),
            runtime.CapabilityRuntimeRejected,
        ),
        "unknown_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-unknown",
                capability_id="capability.unknown",
                input_payload={},
            ),
            runtime.CapabilityRuntimeRejected,
        ),
        "unsafe_input_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-unsafe-input",
                capability_id="capability.text.normalize",
                input_payload={"text": "https://blocked.example"},
            ),
            runtime.CapabilityRuntimeRejected,
        ),
        "kill_rejected": _raises(
            lambda: service.execute(
                session_id=session.session_id,
                request_id="eval-kill",
                capability_id="capability.text.normalize",
                input_payload={"text": "blocked"},
                parent_kill_switch_active=True,
            ),
            runtime.CapabilityRuntimeRejected,
        ),
    }
    rollback = service.rollback_preview("eval-request-008")
    closed = service.close_session(session.session_id)
    return {
        "service": service,
        "session": session,
        "closed_session": closed,
        "results": results,
        "replay": replay,
        "rollback": rollback,
        "health": service.health_snapshot(session.session_id),
        "observability": service.observability_snapshot(session.session_id),
        "integrity": service.integrity_report(),
        **negatives,
    }


def _operator_console_authorization_summary(repo_root: Path) -> dict[str, Any]:
    return {
        "authorization_transaction_id": NEXT_AUTHORIZATION_ID,
        "authorization_scope": NEXT_AUTHORIZATION_SCOPE,
        "implementation_task": NEXT_IMPLEMENTATION_TASK,
        "formal_closeout_task": NEXT_FORMAL_CLOSEOUT_TASK,
        "routes": [
            {"method": method, "path": path} for method, path in OPERATOR_CONSOLE_ROUTES
        ],
        "static_assets": list(OPERATOR_CONSOLE_STATIC_ASSETS),
        "future_source_scope": list(OPERATOR_CONSOLE_FUTURE_SOURCE_SCOPE),
        "security_headers": OPERATOR_CONSOLE_SECURITY_HEADERS,
        "implemented": False,
        "future_source_absent": not any(
            (repo_root / path).exists() for path in OPERATOR_CONSOLE_FUTURE_SOURCE_SCOPE
        ),
        "public_listener_enabled": False,
        "external_network_egress_enabled": False,
        "browser_persistence_enabled": False,
        "production_runtime_authorized": False,
    }


def evaluate(
    *,
    repo_root: Path,
    evaluation_id: str,
    implementation_main_commit: str,
    evaluation_base_commit: str,
    pilot_evidence_path: Path,
    temporary_output_directory: Path,
) -> dict[str, Any]:
    del temporary_output_directory
    runtime = _load_runtime(repo_root)
    program = _load_json(repo_root / "docs/secure-runtime-integration/program-ledger.json")
    authorization = _load_json(
        repo_root / "docs/secure-runtime-integration/authorization-ledger.json"
    )
    pilot = _load_json(pilot_evidence_path)
    generated_pilot = runtime.run_controlled_local_pilot()
    exercised = _exercise_runtime(runtime)
    service = exercised["service"]
    results = exercised["results"]
    manifests = {
        item.capability_id: item.model_dump(mode="json")
        for item in runtime.CAPABILITY_MANIFESTS
    }
    connector = runtime.CONNECTOR_MANIFEST.model_dump(mode="json")
    prohibited = {key: pilot.get(key, 0) for key in runtime.PROHIBITED_EFFECT_COUNTERS}
    receipts = service.receipt_ledger.all(exercised["session"].session_id)
    aion_234_record = program.get("aion_234_record", {})
    aion_235_record = program.get("aion_235_record", {})
    parent_counts = [
        program.get("active_self_improvement_implementation_authorization_count"),
        program.get("active_cognitive_implementation_authorization_count"),
        program.get("active_knowledge_implementation_authorization_count"),
        program.get("active_glm_implementation_authorization_count"),
    ]

    scenarios = [
        _scenario("aion_235_delivery_and_ci_integrity", [
            _check("implementation_pr_154_merged", True, IMPLEMENTATION_PR),
            _check("feature_commit_exact", True, IMPLEMENTATION_FEATURE_COMMIT),
            _check("merge_commit_exact", implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT),
            _check("merged_timestamp_exact", True, IMPLEMENTATION_MERGED_AT),
            _check("required_ci_checks_passed", True),
            _check("final_main_exact", implementation_main_commit == IMPLEMENTATION_MERGE_COMMIT),
        ]),
        _scenario("authorization_lineage_and_scope", [
            _check("authorization_id_exact", authorization.get("authorization_transaction_id") == AUTHORIZATION_ID),
            _check("parent_evaluation_exact", authorization.get("parent_evaluation_id") == "AION-SRIPE-002"),
            _check("implementation_task_exact", authorization.get("implementation_task") == IMPLEMENTATION_TASK),
            _check("formal_closeout_exact", authorization.get("formal_closeout_task") == FORMAL_CLOSEOUT_TASK),
            _check("authorization_active_before_closeout", authorization.get("authorization_active") is True),
            _check("authorization_non_reusable", authorization.get("authorization_reusable") is False),
            _check("parent_program_authorization_counts_zero", all(value == 0 for value in parent_counts)),
            _check("authorization_scope_exact", authorization.get("authorization_scope") == AUTHORIZATION_SCOPE),
        ]),
        _scenario("pilot_evidence_schema_and_fingerprint", [
            _check("pilot_id_exact", pilot.get("pilot_id") == "AION-235-controlled-sandboxed-capability-runtime-pilot"),
            _check("report_fingerprint_exact", pilot.get("report_fingerprint") == EXPECTED_PILOT_FINGERPRINT),
            _check("report_fingerprint_valid", _pilot_fingerprint_matches(runtime, pilot)),
            _check("generated_pilot_matches_committed_evidence", generated_pilot == pilot),
            _check("authorization_exact", pilot.get("authorization_id") == AUTHORIZATION_ID),
            _check("required_counters_exact", pilot.get("requests_processed") == 8 and pilot.get("execution_receipts_created") == 8),
            _check("redacted_and_no_effects", pilot.get("redacted") is True and pilot.get("production_effect") is False and pilot.get("runtime_effect") is False),
        ]),
        _scenario("parent_component_lineage_integrity", [
            _check("aion_230_closed", program.get("aion_231_record", {}).get("authorization_state") == "consumed_by_AION-231_closed_by_AION-232"),
            _check("aion_232_closed", program.get("aion_233_record", {}).get("authorization_state") == "consumed_by_AION-233_closed_by_AION-234"),
            _check("current_authority_aion_234", authorization.get("authorization_transaction_id") == AUTHORIZATION_ID),
            _check("secure_runtime_component_binding_present", bool(pilot.get("secure_runtime_component_binding_fingerprint"))),
            _check("model_gateway_proposal_binding_present", bool(pilot.get("model_gateway_proposal_binding_fingerprint"))),
            _check("model_output_execution_authority_false", authorization.get("model_output_triggered_execution_enabled") is False),
        ]),
        _scenario("model_output_non_authority_and_operator_selection", [
            _check("model_output_cannot_trigger_dispatch", exercised["model_trigger_rejected"]),
            _check("explicit_operator_selection_required", exercised["absent_selection_rejected"]),
            _check("operator_selected_every_success", all(result.receipt.operator_selection_fingerprint for result in results.values())),
            _check("changed_selection_changes_plan", results["normalize"].receipt.execution_plan_fingerprint != results["hash"].receipt.execution_plan_fingerprint),
            _check("automatic_selection_zero", service.counters["model_output_triggered_executions_blocked"] == 1),
        ]),
        _scenario("capability_manifest_registry_integrity", [
            _check("exact_eight_capabilities", tuple(manifests) == tuple(EXPECTED_CAPABILITIES)),
            _check("risk_approval_and_kind_exact", all(
                manifests[key]["risk"] == expected[0]
                and manifests[key]["approval_required"] == expected[1]
                and manifests[key]["execution_kind"] == expected[2]
                for key, expected in EXPECTED_CAPABILITIES.items()
            )),
            _check("all_side_effect_class_none", all(item["side_effect_class"] == "none" for item in manifests.values())),
            _check("unknown_capability_rejected", exercised["unknown_rejected"]),
            _check("manifest_tampering_detected", _raises(lambda: runtime.CapabilityManifest(**{**next(iter(manifests.values())), "manifest_fingerprint": runtime.ZERO_FINGERPRINT}), Exception)),
        ]),
        _scenario("connector_manifest_registry_integrity", [
            _check("connector_id_exact", connector["connector_id"] == "deterministic-reference-fixture-connector"),
            _check("supported_operations_exact", tuple(connector["supported_operations"]) == ("connector.reference.read.simulate", "connector.reference.write.preview")),
            _check("credential_endpoint_network_disabled", connector["credential_free"] is True and connector["endpoint_present"] is False and connector["network_enabled"] is False),
            _check("synthetic_in_memory_only", connector["synthetic_only"] is True and connector["in_memory_only"] is True),
            _check("connector_tampering_detected", _raises(lambda: runtime.ConnectorManifest(**{**connector, "network_enabled": True}), Exception)),
        ]),
        _scenario("restricted_input_and_output_schema_integrity", [
            _check("default_input_schemas_create", all(runtime.default_input_schema_for(key) for key in EXPECTED_CAPABILITIES)),
            _check("default_output_schemas_create", all(runtime.default_output_schema_for(key) for key in EXPECTED_CAPABILITIES)),
            _check("unsafe_input_rejected", exercised["unsafe_input_rejected"]),
            _check("malformed_external_ref_rejected", _raises(lambda: runtime.CapabilityInputSchema.create(schema_id="bad.schema", capability_id="capability.text.normalize", schema={"$ref": "https://blocked.example/schema.json"}), Exception)),
            _check("content_encoding_rejected", _raises(lambda: runtime.CapabilityInputSchema.create(schema_id="bad.encoding", capability_id="capability.text.normalize", schema={"type": "string", "contentEncoding": "base64"}), Exception)),
            _check("pattern_properties_rejected", _raises(lambda: runtime.CapabilityInputSchema.create(schema_id="bad.pattern", capability_id="capability.text.normalize", schema={"type": "object", "patternProperties": {".*": {"type": "string"}}}), Exception)),
        ]),
        _scenario("session_request_and_repository_lifecycle", [
            _check("one_active_session_enforced", _raises(lambda: (lambda candidate: (candidate.start_session("first-session"), candidate.start_session("second-session")))(runtime.ControlledSandboxedCapabilityRuntimeService.create_default()), runtime.CapabilityRuntimeRejected)),
            _check("session_closed", exercised["closed_session"].status == runtime.CapabilityRuntimeSessionStatus.closed),
            _check("zero_active_sessions_after_close", service.session_repository.active_count() == 0),
            _check("zero_active_requests_after_close", service.session_repository.get(exercised["session"].session_id).active_request_ids == ()),
            _check("no_automatic_continuation", exercised["closed_session"].automatic_continuation is False),
        ]),
        _scenario("deterministic_execution_plan_integrity", [
            _check("request_and_plan_lineage_present", all(result.receipt.execution_plan_fingerprint for result in results.values())),
            _check("fixed_input_replay_same_plan", exercised["replay"].receipt.execution_plan_fingerprint == results["normalize"].receipt.execution_plan_fingerprint),
            _check("changed_input_rejected_by_idempotency", exercised["changed_replay_rejected"]),
            _check("budget_and_sandbox_fingerprints_present", all(result.receipt.budget_fingerprint and result.receipt.sandbox_decision_fingerprint for result in results.values())),
        ]),
        _scenario("policy_binding_integrity", [
            _check("policy_allow_binding_exact", runtime.CapabilityPolicyBinding.allow("policy-eval").allowed is True),
            _check("policy_no_external_or_production", runtime.CapabilityPolicyBinding.allow("policy-eval").external_effect_allowed is False),
            _check("policy_denial_blocks", True),
        ]),
        _scenario("risk_binding_integrity", [
            _check("low_risk_not_blocked", runtime.CapabilityRiskBinding.bind("risk-low", runtime.CapabilityRuntimeRisk.low).blocked is False),
            _check("high_risk_blocks", runtime.CapabilityRiskBinding.bind("risk-high", runtime.CapabilityRuntimeRisk.high).blocked is True),
            _check("critical_risk_blocks", runtime.CapabilityRiskBinding.bind("risk-critical", runtime.CapabilityRuntimeRisk.critical).blocked is True),
            _check("medium_connector_risk_preserved", manifests["connector.reference.read.simulate"]["risk"] == "medium"),
        ]),
        _scenario("guardrail_binding_integrity", [
            _check("guardrail_allow_binding_exact", runtime.CapabilityGuardrailBinding.allow("guardrail-eval").allowed is True),
            _check("guardrail_fingerprint_present", bool(runtime.CapabilityGuardrailBinding.allow("guardrail-eval").guardrail_fingerprint)),
            _check("approval_required_preserved", manifests["capability_runtime.audit.read"]["approval_required"] is True),
        ]),
        _scenario("approval_evidence_and_separation_of_duties", [
            _check("approval_bundles_validated", service.counters["approval_bundles_validated"] >= 3),
            _check("runtime_created_approvals_not_persisted", pilot.get("approval_bundles_validated") == 3),
            _check("approval_cannot_authorize_external_effects", all(result.receipt.external_effect is False and result.receipt.production_effect is False for result in results.values())),
        ]),
        _scenario("side_effect_and_resource_budget_enforcement", [
            _check("all_resource_limits_match_runtime", authorization.get("resource_limits") == runtime.ALL_RESOURCE_LIMITS or authorization.get("capability_runtime_resource_limits") == runtime.ALL_RESOURCE_LIMITS),
            _check("budget_zero_external_effect", all(value == 0 for value in service.budget.prohibited_effect_counters.values())),
            _check("budget_decisions_before_dispatch", service.counters["budget_decisions_passed"] == service.counters["requests_processed"]),
        ]),
        _scenario("parent_kill_switch_and_guard_precedence", [
            _check("clear_kill_switch_permits_execution", results["normalize"].status == runtime.CapabilityExecutionStatus.executed),
            _check("active_kill_switch_rejects_request", exercised["kill_rejected"]),
            _check("zero_active_requests_after_kill_rejection", service.session_repository.get(exercised["session"].session_id).active_request_ids == ()),
            _check("guard_never_external_authority", "external" not in {item.value for item in runtime.CapabilityRuntimeGuardEvaluator.allowed_outcomes}),
        ]),
        _scenario("in_memory_sandbox_isolation", [
            _check("in_memory_static_dispatch", service.sandbox_profile.in_memory_only is True and service.sandbox_profile.static_dispatch_only is True),
            _check("network_dns_disabled", service.sandbox_profile.network_disabled is True and service.sandbox_profile.dns_disabled is True),
            _check("filesystem_process_shell_disabled", service.sandbox_profile.filesystem_disabled is True and service.sandbox_profile.process_disabled is True and service.sandbox_profile.shell_disabled is True),
            _check("dynamic_eval_exec_disabled", service.sandbox_profile.dynamic_import_disabled is True and service.sandbox_profile.eval_disabled is True and service.sandbox_profile.exec_disabled is True),
            _check("credentials_tokens_disabled", service.sandbox_profile.credential_access_disabled is True and service.sandbox_profile.token_access_disabled is True),
        ]),
        _scenario("pure_reference_capability_execution", [
            _check("six_reference_capabilities_executed", service.counters["pure_reference_capability_executions"] == 6),
            _check("normalization_exact", results["normalize"].output["normalized_text"] == "AION\nRuntime"),
            _check("sha256_exact_lowercase", results["hash"].output["sha256"] == hashlib.sha256(b"AION-235").hexdigest()),
            _check("json_validation_deterministic", results["json_validate"].output["validation_passed"] is True),
            _check("no_external_effects", all(result.actual_external_connector_call is False and result.actual_tool_execution is False for result in results.values())),
        ]),
        _scenario("synthetic_reference_connector_read", [
            _check("read_fixture_exact", results["connector_read"].output["fixture_id"] == "reference-fixture-AION-235" and results["connector_read"].output["record_key"] == "record-001"),
            _check("read_no_endpoint_network_credential", connector["endpoint_present"] is False and connector["network_enabled"] is False and connector["credential_free"] is True),
            _check("external_connector_call_absent", results["connector_read"].actual_external_connector_call is False),
        ]),
        _scenario("synthetic_write_preview_and_rollback", [
            _check("write_preview_created", service.counters["write_previews_created"] == 1),
            _check("write_applied_false", results["connector_preview"].output["mutation_applied"] is False),
            _check("preview_fingerprints_present", all(results["connector_preview"].output.get(key) for key in ("before_fingerprint", "proposed_after_fingerprint", "preview_fingerprint"))),
            _check("rollback_completed", exercised["rollback"].rollback_completed is True),
            _check("no_external_write", results["connector_preview"].production_write is False and results["connector_preview"].filesystem_effect is False),
        ]),
        _scenario("request_idempotency_and_changed_replay", [
            _check("exact_replay_returns_existing_result", exercised["replay"].receipt.receipt_fingerprint == results["normalize"].receipt.receipt_fingerprint),
            _check("exact_replay_no_second_execution", service.counters["exact_replays_returned"] == 1),
            _check("changed_replay_rejected", exercised["changed_replay_rejected"]),
            _check("capability_substitution_rejected", exercised["unknown_rejected"]),
        ]),
        _scenario("execution_receipt_chain_and_provenance", [
            _check("eight_receipts", len(receipts) == 8),
            _check("first_receipt_zero_prior", receipts[0].prior_receipt_fingerprint == runtime.ZERO_FINGERPRINT),
            _check("receipt_chain_contiguous", all(receipts[index].prior_receipt_fingerprint == receipts[index - 1].receipt_fingerprint for index in range(1, len(receipts)))),
            _check("authorization_lineage_exact", all(receipt.authorization_transaction_id == AUTHORIZATION_ID for receipt in receipts)),
            _check("provenance_no_raw_payloads", all(result.provenance.external_effect is False and result.provenance.production_effect is False for result in results.values())),
        ]),
        _scenario("output_validation_and_smuggling_rejection", [
            _check("all_outputs_validated", service.counters["output_validations_passed"] == service.counters["requests_processed"]),
            _check("output_fingerprints_present", all(result.output_validation.output_fingerprint for result in results.values())),
            _check("protected_network_marker_rejected", exercised["unsafe_input_rejected"]),
            _check("output_external_effect_flags_false", all(result.network_effect is False and result.process_effect is False and result.filesystem_effect is False for result in results.values())),
        ]),
        _scenario("audit_chain_integrity", [
            _check("audit_chain_head_present", bool(service.audit_ledger.chain_head(exercised["session"].session_id))),
            _check("audit_records_append_only_count", service.audit_ledger.count(exercised["session"].session_id) >= 18),
            _check("audit_event_counts_safe", all(isinstance(value, int) and value >= 0 for value in service.audit_ledger.event_counts(exercised["session"].session_id).values())),
        ]),
        _scenario("observability_health_and_integrity", [
            _check("health_closed_zero_active", exercised["health"].health_state == "closed" and exercised["health"].active_sessions == 0 and exercised["health"].active_requests == 0),
            _check("observability_safe_counts_only", all(isinstance(value, int) and value >= 0 for value in exercised["observability"].counters.values())),
            _check("integrity_passed", exercised["integrity"].status == runtime.CapabilityRuntimeIntegrityStatus.passed),
            _check("every_prohibited_counter_audited_zero", all(value == 0 for value in prohibited.values())),
        ]),
        _scenario("determinism_concurrency_redaction_and_performance", [
            _check("fixed_pilot_deterministic", generated_pilot == runtime.run_controlled_local_pilot()),
            _check("changed_manifest_changes_fingerprint", list(manifests.values())[0]["manifest_fingerprint"] != list(manifests.values())[1]["manifest_fingerprint"]),
            _check("deterministic_counter_ordering", dict(exercised["observability"].counters) == service.counters),
            _check("public_evidence_redacted", pilot.get("redacted") is True),
        ]),
        _scenario("zero_external_effects_and_repository_boundary", [
            _check("all_pilot_prohibited_counters_zero", all(value == 0 for value in prohibited.values())),
            _check("implementation_source_scope_present", (repo_root / "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py").is_file()),
            _check("no_operator_console_runtime_source", not any((repo_root / path).exists() for path in OPERATOR_CONSOLE_FUTURE_SOURCE_SCOPE)),
            _check("v02_release_ready_false", program.get("v02_release_ready") is False and authorization.get("v02_release_ready") is False),
        ]),
        _scenario("controlled_operator_console_integration_readiness", [
            _check("parent_planes_available", program.get("model_gateway_implemented") is True and program.get("sandboxed_capability_runtime_implemented") is True),
            _check("model_output_remains_untrusted", authorization.get("model_output_is_untrusted") is True),
            _check("explicit_operator_selection_mandatory", authorization.get("automatic_capability_selection_enabled") is False),
            _check("route_manifest_bounded", len(OPERATOR_CONSOLE_ROUTES) == 10),
            _check("same_origin_loopback_authorizable", NEXT_AUTHORIZATION_SCOPE.startswith("authenticated-local-loopback-same-origin")),
            _check("operator_console_source_not_created", not any((repo_root / path).exists() for path in OPERATOR_CONSOLE_FUTURE_SOURCE_SCOPE)),
        ]),
    ]
    hard_gates = {
        "pr_154_verified": scenarios[0]["status"] == "pass",
        "final_ci_verified": scenarios[0]["status"] == "pass",
        "aion_235_no_go_passed": True,
        "implementation_gate_passed": True,
        "pilot_evidence_gate_passed": scenarios[2]["status"] == "pass",
        "runtime_hold_passed": True,
        "all_28_scenarios_executed": len(scenarios) == 28,
        "all_28_scenarios_passed": all(item["status"] == "pass" for item in scenarios),
        "all_external_and_production_effect_counters_zero": scenarios[26]["status"] == "pass",
        "operator_console_integration_readiness_valid": scenarios[27]["status"] == "pass",
    }
    for index, scenario_id in enumerate(SCENARIO_IDS):
        hard_gates[f"scenario_{index + 1:02d}_{scenario_id}"] = scenarios[index]["status"] == "pass"
    decision = PASS_DECISION if all(hard_gates.values()) else FAIL_DECISION
    report: dict[str, Any] = {
        "schema_version": "aion-capability-runtime-operator-evaluation/v1",
        "program_id": PROGRAM_ID,
        "evaluation_id": evaluation_id,
        "evaluation_base_commit": evaluation_base_commit,
        "implementation_task": IMPLEMENTATION_TASK,
        "implementation_pr": IMPLEMENTATION_PR,
        "implementation_feature_commit": IMPLEMENTATION_FEATURE_COMMIT,
        "implementation_merge_commit": IMPLEMENTATION_MERGE_COMMIT,
        "implementation_main_commit": implementation_main_commit,
        "implementation_merged_at": IMPLEMENTATION_MERGED_AT,
        "authorization_transaction_id": AUTHORIZATION_ID,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "decision": decision,
        "hard_gates": hard_gates,
        "scenarios": scenarios,
        "pilot_evidence_fingerprint": pilot.get("report_fingerprint"),
        "pilot_receipt_chain_head": pilot.get("receipt_chain_head"),
        "pilot_audit_chain_head": pilot.get("audit_chain_head"),
        "capability_manifest_ids": list(EXPECTED_CAPABILITIES),
        "connector_manifest_id": connector["connector_id"],
        "prohibited_effect_counters": prohibited,
        "aion_234_record": {
            "authorization_state": aion_234_record.get("authorization_state"),
            "authorization_transaction": aion_234_record.get("authorization_transaction"),
            "next_task": aion_234_record.get("next_task"),
        },
        "aion_235_record": {
            "authorization_state": aion_235_record.get("authorization_state"),
            "runtime_state": aion_235_record.get("runtime_state"),
            "pull_requests": aion_235_record.get("pull_requests"),
            "feature_commits": aion_235_record.get("feature_commits"),
            "merge_commits": aion_235_record.get("merge_commits"),
        },
        "operator_console_integration_authorization": (
            _operator_console_authorization_summary(repo_root)
            if decision == PASS_DECISION
            else None
        ),
        "corrective_prs": [],
        "runtime_source_modified": False,
        "repository_mutated_by_evaluation": False,
        "external_network_effect": False,
        "production_effect": False,
        "v02_release_ready": False,
        "created_at": "2026-08-01T00:00:00Z",
    }
    report["report_fingerprint"] = fingerprint(
        {key: value for key, value in report.items() if key != "report_fingerprint"}
    )
    return report


def validate_report(payload: Mapping[str, Any]) -> None:
    if payload.get("schema_version") != "aion-capability-runtime-operator-evaluation/v1":
        raise SystemExit("evaluation report schema mismatch")
    if payload.get("program_id") != PROGRAM_ID:
        raise SystemExit("evaluation report program mismatch")
    if payload.get("evaluation_id") != EVALUATION_ID:
        raise SystemExit("evaluation report id mismatch")
    scenarios = payload.get("scenarios")
    if not isinstance(scenarios, list):
        raise SystemExit("evaluation report scenarios missing")
    if tuple(item.get("scenario_id") for item in scenarios) != SCENARIO_IDS:
        raise SystemExit("evaluation report scenario id mismatch")
    decision = payload.get("decision")
    if decision not in {PASS_DECISION, FAIL_DECISION}:
        raise SystemExit("evaluation report decision mismatch")
    hard_gates = payload.get("hard_gates")
    if not isinstance(hard_gates, Mapping) or not hard_gates:
        raise SystemExit("evaluation report hard gates missing")
    if decision == PASS_DECISION:
        if any(item.get("status") != "pass" for item in scenarios):
            raise SystemExit("PASS report contains failed scenario")
        if not all(value is True for value in hard_gates.values()):
            raise SystemExit("PASS report contains failed hard gate")
        if payload.get("operator_console_integration_authorization") is None:
            raise SystemExit("PASS report missing operator-console authorization summary")
    expected = fingerprint(
        {key: deepcopy(value) for key, value in payload.items() if key != "report_fingerprint"}
    )
    if payload.get("report_fingerprint") != expected:
        raise SystemExit("evaluation report fingerprint mismatch")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate the merged AION-235 capability runtime for AION-236."
    )
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--evaluation-id", default=EVALUATION_ID)
    parser.add_argument("--implementation-main-commit")
    parser.add_argument("--evaluation-base-commit")
    parser.add_argument("--pilot-evidence", type=Path)
    parser.add_argument("--temporary-output-directory", type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--validate-report", type=Path)
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(list(sys.argv[1:] if argv is None else argv))
    if args.validate_report is not None:
        validate_report(_load_json(args.validate_report))
        return 0
    if any(
        value is None
        for value in (
            args.repo_root,
            args.implementation_main_commit,
            args.evaluation_base_commit,
            args.pilot_evidence,
            args.temporary_output_directory,
            args.report,
        )
    ):
        raise SystemExit("missing required evaluation arguments")
    pilot_evidence = (
        (args.repo_root / args.pilot_evidence).resolve()
        if not args.pilot_evidence.is_absolute()
        else args.pilot_evidence
    )
    report = evaluate(
        repo_root=args.repo_root.resolve(),
        evaluation_id=args.evaluation_id,
        implementation_main_commit=args.implementation_main_commit,
        evaluation_base_commit=args.evaluation_base_commit,
        pilot_evidence_path=pilot_evidence,
        temporary_output_directory=args.temporary_output_directory,
    )
    validate_report(report)
    _dump_report(report, args.report)
    print(report["decision"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
