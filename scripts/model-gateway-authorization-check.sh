#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/portable-search.sh"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
./scripts/model-gateway-authorization-no-go-regression.sh
"$PYTHON_BIN" scripts/lib/secure_runtime_foundation_operator_evaluation.py --validate-report examples/secure-runtime-integration/runtime-foundation-operator-evaluation-report.json
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json, os
from pathlib import Path
ROOT = Path(os.environ["AION_REPO_ROOT"])
REPORT = json.loads((ROOT / "examples/secure-runtime-integration/runtime-foundation-operator-evaluation-report.json").read_text())
PROGRAM = json.loads((ROOT / "docs/secure-runtime-integration/program-ledger.json").read_text())
AUTH = json.loads((ROOT / "docs/secure-runtime-integration/authorization-ledger.json").read_text())
EXAMPLE = json.loads((ROOT / "examples/secure-runtime-integration/model-gateway-authorization.json").read_text())
DECISION = "SECURE_LOCAL_OPERATOR_RUNTIME_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_MODEL_GATEWAY_AUTHORIZATION"
SCOPE = "authenticated-local-model-request-envelope-provider-model-manifest-closed-allowlist-context-token-budget-redaction-routing-fallback-retry-circuit-breaker-cost-latency-estimation-structured-output-validation-untrusted-output-provenance-deterministic-reference-provider-no-egress-core"
AION231 = "AION-230-SRI-0001"; AION232 = "AION-232-SRI-0002"
A231_FEATURE = "45540009d03f60d7477330a88946e73705ee60e5"; A231_MERGE = "8bb9af29cc2cf960d9efdfe2ee323d7245812747"
if REPORT["decision"] != DECISION or REPORT["evaluation_passed"] is not True:
    raise SystemExit("operator evaluation did not record exact PASS")
if REPORT["scenario_count"] != 28 or not all(item["passed"] is True for item in REPORT["scenario_results"]):
    raise SystemExit("not every scenario passed")
if not all(item["passed"] is True for item in REPORT["hard_gate_results"]):
    raise SystemExit("not every hard gate passed")
for key in ("network_calls", "model_provider_calls", "connector_calls", "actual_tool_executions", "credentials_persisted", "tokens_persisted", "runtime_created_approvals", "production_writes", "production_memory_writes", "production_policy_mutations", "cognitive_memory_writes", "actual_belief_creations", "actual_belief_mutations", "source_mutations", "git_operations", "deployments", "model_weight_changes", "active_sessions_after_evaluation", "active_requests_after_evaluation"):
    if REPORT.get(key) != 0:
        raise SystemExit(f"report counter must be zero: {key}")
closed = next(item for item in AUTH["records"] if item["authorization_transaction_id"] == AION231)
if closed["authorization_active"] is not False or closed["authorization_consumed"] is not True or closed["authorization_expired"] is not True or closed["authorization_reusable"] is not False:
    raise SystemExit("AION-230-SRI-0001 lifecycle mismatch")
if closed["authorization_consumed_by_task"] != "AION-231" or closed["authorization_consumed_by_prs"] != [149] or closed["authorization_consumed_by_feature_commits"] != [A231_FEATURE] or closed["authorization_consumed_by_merge_commits"] != [A231_MERGE] or closed["authorization_closed_by_task"] != "AION-232":
    raise SystemExit("AION-230-SRI-0001 lineage mismatch")
if EXAMPLE["authorization_transaction_id"] != AION232 or EXAMPLE["approval_record_id"] != AION232:
    raise SystemExit("AION-232-SRI-0002 example missing")
if EXAMPLE["candidate_id"] != "controlled-provider-neutral-model-gateway-core" or EXAMPLE["workstream"] != "secure-runtime-model-gateway":
    raise SystemExit("candidate/workstream mismatch")
if EXAMPLE["implementation_task"] != "AION-233" or EXAMPLE["formal_closeout_task"] != "AION-234" or EXAMPLE["authorization_scope"] != SCOPE:
    raise SystemExit("task/scope mismatch")

closed_aion232 = next(item for item in AUTH["records"] if item["authorization_transaction_id"] == AION232)
post_closeout_states = {
    "model_gateway_evaluated_sandboxed_capability_runtime_authorized_not_implemented": (
        "AION-234-SRI-0003",
        "AION-235",
    ),
    "sandboxed_capability_runtime_implemented_reference_only_pending_closeout": (
        "AION-234-SRI-0003",
        "AION-235",
    ),
    "capability_runtime_evaluated_operator_console_integration_authorized_not_implemented": (
        "AION-236-SRI-0004",
        "AION-237",
    ),
    "operator_console_integrated_local_runtime_implemented_pending_final_evaluation": (
        "AION-236-SRI-0004",
        "AION-237",
    ),
}
if PROGRAM.get("program_state") in post_closeout_states:
    if closed_aion232["authorization_active"] is not False or closed_aion232["authorization_consumed"] is not True or closed_aion232["authorization_expired"] is not True or closed_aion232["authorization_reusable"] is not False:
        raise SystemExit("AION-232 closeout lifecycle mismatch")
    if closed_aion232["authorization_consumed_by_task"] != "AION-233" or closed_aion232["authorization_closed_by_task"] != "AION-234":
        raise SystemExit("AION-232 closeout lineage mismatch")
    expected_auth, expected_task = post_closeout_states[PROGRAM["program_state"]]
    if AUTH["active_sri_implementation_authorization_count"] != 1 or AUTH["active_sri_implementation_authorization"] != expected_auth or AUTH["active_sri_implementation_task"] != expected_task:
        raise SystemExit("sole active post-closeout SRI authorization mismatch")
elif PROGRAM.get("program_state") == "secure_runtime_integration_program_complete":
    if closed_aion232["authorization_active"] is not False or closed_aion232["authorization_consumed"] is not True or closed_aion232["authorization_expired"] is not True or closed_aion232["authorization_reusable"] is not False:
        raise SystemExit("AION-232 closeout lifecycle mismatch")
    if closed_aion232["authorization_consumed_by_task"] != "AION-233" or closed_aion232["authorization_closed_by_task"] != "AION-234":
        raise SystemExit("AION-232 closeout lineage mismatch")
    if AUTH["active_sri_implementation_authorization_count"] != 0 or AUTH["active_sri_implementation_authorization"] is not None or AUTH["active_sri_implementation_task"] is not None:
        raise SystemExit("completed SRI authorization state mismatch")
else:
    if AUTH["authorization_transaction_id"] != AION232 or AUTH["approval_record_id"] != AION232:
        raise SystemExit("AION-232-SRI-0002 missing")
    if AUTH["authorization_active"] is not True or AUTH["authorization_consumed"] is not False or AUTH["authorization_expired"] is not False or AUTH["authorization_reusable"] is not False:
        raise SystemExit("AION-232 authorization lifecycle mismatch")
    if AUTH["active_sri_implementation_authorization_count"] != 1 or AUTH["active_sri_implementation_authorization"] != AION232 or AUTH["active_sri_implementation_task"] != "AION-233":
        raise SystemExit("sole active SRI authorization mismatch")
if PROGRAM["formal_closeout_task"] not in {"AION-234", "AION-236", "AION-238", None} or PROGRAM["model_gateway_authorized"] is not True or PROGRAM["model_gateway_implemented"] is not True:
    raise SystemExit("program model-gateway state mismatch")
if PROGRAM.get("model_gateway_state") not in {
    "implemented_provider_neutral_reference_simulation_only_pending_AION-234_closeout",
    "implemented_provider_neutral_reference_simulation_only",
}:
    raise SystemExit("program model-gateway implemented state mismatch")
if not all(AUTH["model_gateway_authorized_capabilities"].values()):
    raise SystemExit("not every model-gateway authorized capability is true")
if any(AUTH["model_gateway_prohibited_capabilities"].values()):
    raise SystemExit("a prohibited model-gateway capability is true")
if any(value != 0 for key, value in AUTH["model_gateway_resource_limits"].items() if key.startswith("maximum_public_network") or key in {"maximum_model_provider_calls", "maximum_provider_sdk_calls", "maximum_provider_endpoint_connections", "maximum_provider_credentials_read", "maximum_api_keys_persisted", "maximum_tokens_persisted", "maximum_live_model_sessions", "maximum_tool_calls", "maximum_function_calls", "maximum_connector_calls", "maximum_actual_tool_executions", "maximum_deployments", "maximum_model_weight_changes"}):
    raise SystemExit("zero-effect resource limit mismatch")
PY

echo "controlled model gateway authorization PASS"
