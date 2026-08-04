#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

./scripts/external-cognition-foundation-no-go-regression.sh
./scripts/external-cognition-fixture-pilot-evidence-check.sh

if [[ -n "${PYTEST_CURRENT_TEST:-}" ]] || [[ "${AION_EXTERNAL_COGNITION_FOUNDATION_SKIP_PYTEST:-}" == "1" ]]; then
  echo "PASS: focused AION-246 pytest deferred to outer test context"
else
  "$PYTHON_BIN" -m pytest services/brain-api/tests/test_external_cognition_foundation_aion246.py -q
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import stat
import sys
import tomllib
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
sys.path.insert(0, str(ROOT / "services/brain-api/src"))

from aion_brain.contracts.external_cognition import (  # noqa: E402
    AUTHORIZATION_TRANSACTION_ID,
    FINAL_PLANNED_TASK,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    PROHIBITED_EFFECT_COUNTERS,
)
from aion_brain.external_cognition import ControlledExternalCognitionService  # noqa: E402
from aion_brain.external_cognition.integrity import (  # noqa: E402
    default_budgets,
    default_route_policies,
    default_structured_output_schemas,
)

EXPECTED_MAIN = "d7fe689bfe39a98688784758ceb2b7130ca949bd"
EXPECTED_STATE = "external_cognition_gateway_foundation_implemented_disabled_pending_AION-247_closeout"
EXPECTED_POST_EVALUATION_STATE = (
    "external_cognition_foundation_evaluated_live_provider_pilot_authorized_not_implemented"
)
EXPECTED_GATEWAY_STATE = "implemented_disabled_deterministic_fixture_only_pending_AION-247_closeout"
EXPECTED_POST_EVALUATION_GATEWAY_STATE = (
    "implemented_disabled_deterministic_fixture_only_operator_evaluated_live_provider_pilot_authorized_not_implemented"
)
EXPECTED_VERSION = "0.3.0.dev0"
REQUIRED_SOURCE = {
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
PROHIBITED_SOURCE = {
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
}
REQUIRED_DOCS = {
    "docs/adaptive-intelligence/external-cognition-foundation-implementation.md",
    "docs/adaptive-intelligence/external-cognition-contracts.md",
    "docs/adaptive-intelligence/external-cognition-component-lineage.md",
    "docs/adaptive-intelligence/provider-manifests.md",
    "docs/adaptive-intelligence/model-manifests.md",
    "docs/adaptive-intelligence/message-normalization.md",
    "docs/adaptive-intelligence/request-response-envelopes.md",
    "docs/adaptive-intelligence/structured-output-validation.md",
    "docs/adaptive-intelligence/external-cognition-routing.md",
    "docs/adaptive-intelligence/external-cognition-budgets.md",
    "docs/adaptive-intelligence/external-cognition-trust.md",
    "docs/adaptive-intelligence/external-cognition-redaction.md",
    "docs/adaptive-intelligence/external-cognition-circuit-breaker.md",
    "docs/adaptive-intelligence/external-cognition-replay.md",
    "docs/adaptive-intelligence/external-cognition-observability.md",
    "docs/adaptive-intelligence/external-cognition-audit.md",
    "docs/adaptive-intelligence/external-cognition-fixture-pilot.md",
    "docs/adaptive-intelligence/external-cognition-security-review.md",
    "docs/adaptive-intelligence/external-cognition-operator-runbook.md",
    "docs/adaptive-intelligence/aion-246-checklist.md",
    "docs/release/v03-external-cognition-foundation.md",
    "docs/release/v03-external-cognition-fixture-pilot.md",
    "docs/release/v03-external-cognition-security-evidence.md",
    "docs/release/v03-external-cognition-runtime-hold.md",
    "docs/release/v03-external-cognition-checklist.md",
    "docs/adr/0210-controlled-provider-neutral-external-cognition-gateway-foundation.md",
}
REQUIRED_ARTIFACTS = {
    "examples/adaptive-intelligence/program-authorization.json",
    "examples/adaptive-intelligence/external-cognition-foundation-authorization.json",
    "examples/adaptive-intelligence/program-roadmap.json",
    "examples/adaptive-intelligence/runtime-hold.json",
    "examples/adaptive-intelligence/external-cognition-runtime-hold.json",
    "examples/adaptive-intelligence/external-cognition-contract-examples.json",
    "examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json",
    "operator-console-static/demo-data/adaptive-intelligence-program.json",
    "operator-console-static/demo-data/external-cognition-authorization.json",
    "operator-console-static/demo-data/adaptive-intelligence-runtime-hold.json",
    "operator-console-static/demo-data/external-cognition-foundation.json",
    "operator-console-static/demo-data/external-cognition-static-console-evidence.json",
}
EXPECTED_RESOURCE_LIMITS = {
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


def load_json(path: str) -> dict:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


for path in sorted(REQUIRED_SOURCE | REQUIRED_DOCS | REQUIRED_ARTIFACTS):
    if not (ROOT / path).is_file():
        raise SystemExit(f"missing AION-246 required file: {path}")

runner = ROOT / "scripts/external-cognition-fixture-local-run.py"
if not runner.stat().st_mode & stat.S_IXUSR:
    raise SystemExit("external cognition fixture runner is not executable")

for path in sorted(PROHIBITED_SOURCE):
    if (ROOT / path).exists():
        raise SystemExit(f"prohibited AION-246 runtime/provider file exists: {path}")

program = load_json("docs/adaptive-intelligence/program-ledger.json")
auth = load_json("docs/adaptive-intelligence/authorization-ledger.json")
records = {
    item.get("authorization_transaction_id"): item for item in auth.get("records", [])
}
record = records.get(AUTHORIZATION_TRANSACTION_ID)
successor = records.get("AION-247-AI-0002")
hold = load_json("examples/adaptive-intelligence/external-cognition-runtime-hold.json")
evidence = load_json("examples/adaptive-intelligence/external-cognition-fixture-pilot-evidence.json")

if program["program_id"] != PROGRAM_ID or auth["program_id"] != PROGRAM_ID:
    raise SystemExit("adaptive intelligence program ID mismatch")
if record is None or record["authorization_transaction_id"] != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-245-AI-0001 authorization record missing")
if record["approval_record_id"] != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-245-AI-0001 approval record mismatch")

program_state = program["program_state"]
post_evaluation = program_state == EXPECTED_POST_EVALUATION_STATE
expected_gateway_states = {EXPECTED_GATEWAY_STATE, EXPECTED_POST_EVALUATION_GATEWAY_STATE}
for payload_name, payload in (("program", program), ("authorization", record), ("hold", hold)):
    for key, expected in {
        "external_cognition_gateway_implemented": True,
        "deterministic_fixture_pilot_completed": True,
    }.items():
        if payload.get(key) != expected:
            raise SystemExit(f"{payload_name} mismatch {key}: {payload.get(key)!r}")
    if payload.get("external_cognition_gateway_state") not in expected_gateway_states:
        raise SystemExit(f"{payload_name} external cognition gateway state mismatch")

if program_state not in {EXPECTED_STATE, EXPECTED_POST_EVALUATION_STATE}:
    raise SystemExit("AION-246 implemented-disabled program state mismatch")
if auth["program_state"] not in {EXPECTED_STATE, EXPECTED_POST_EVALUATION_STATE}:
    raise SystemExit("AION-246 authorization ledger program state mismatch")
if program["current_state"]["current_main_commit"] not in {EXPECTED_MAIN, "27d6ad15a043940bf537caec72cf7de7c74f6dc2"}:
    raise SystemExit("current main commit reconciliation mismatch")
if program["current_state"]["current_released_prerelease"] != "aion-v0.2.0-rc.1":
    raise SystemExit("RC1 prerelease marker changed")
if program["current_state"]["production_runtime_authorized"] is not False:
    raise SystemExit("production runtime authorization must remain false")

for payload_name, payload in (("program", program), ("authorization", record)):
    if any(value is not True for value in payload["approved_capabilities"].values()):
        raise SystemExit(f"{payload_name} approved capability is not true")
    if any(value is not False for value in payload["prohibited_capabilities"].values()):
        raise SystemExit(f"{payload_name} prohibited capability is not false")
if not post_evaluation and set(program["approved_capabilities"]) != set(record["approved_capabilities"]):
    raise SystemExit("approved capability key set mismatch")
if not post_evaluation and set(program["prohibited_capabilities"]) != set(record["prohibited_capabilities"]):
    raise SystemExit("prohibited capability key set mismatch")
if post_evaluation:
    if successor is None:
        raise SystemExit("AION-247 successor authorization missing")
    if successor.get("authorization_active") is not True:
        raise SystemExit("AION-247 successor authorization must be active")
    if successor.get("implementation_task") != "AION-248":
        raise SystemExit("AION-247 successor implementation task mismatch")
    if any(value is not False for value in successor["prohibited_capabilities"].values()):
        raise SystemExit("AION-247 successor prohibited capability is not false")
if program["resource_limits"] != EXPECTED_RESOURCE_LIMITS:
    raise SystemExit("AION-246 resource limits changed")

expected_lifecycle = {
    "authorization_transaction_approved": True,
    "explicit_approval_record_approval": True,
    "implementation_authorization_approved": True,
    "implementation_go_status": True,
    "implementation_no_go_status": False,
    "authorization_reusable": False,
}
if post_evaluation:
    expected_lifecycle.update(
        {
            "authorization_active": False,
            "authorization_consumed": True,
            "authorization_expired": True,
        }
    )
else:
    expected_lifecycle.update(
        {
            "authorization_active": True,
            "authorization_consumed": False,
            "authorization_expired": False,
        }
    )
for key, expected in expected_lifecycle.items():
    if record.get(key) != expected:
        raise SystemExit(f"authorization lifecycle mismatch {key}: {record.get(key)!r}")

aion245 = program["aion_245_record"]
if aion245["pull_requests"] != [165] or aion245["ci_result"] != "pass":
    raise SystemExit("AION-245 PR/CI reconciliation mismatch")
if aion245["merge_commits"] != [EXPECTED_MAIN]:
    raise SystemExit("AION-245 merge commit mismatch")
if aion245["runtime_source_changes"] != 0 or aion245["dependency_changes"] != 0:
    raise SystemExit("AION-245 source/dependency reconciliation changed")

aion246 = program["aion_246_record"]
if aion246["task_id"] != IMPLEMENTATION_TASK:
    raise SystemExit("AION-246 record missing")
if aion246["runtime_state"] not in {
    EXPECTED_GATEWAY_STATE,
    "external_cognition_gateway_foundation_implemented_disabled_fixture_only",
}:
    raise SystemExit("AION-246 runtime state mismatch")
if aion246["authorization_transaction"] != AUTHORIZATION_TRANSACTION_ID:
    raise SystemExit("AION-246 authorization mismatch")
if aion246["prohibited_effect_counters"] != PROHIBITED_EFFECT_COUNTERS:
    raise SystemExit("AION-246 prohibited effect counters changed")
if aion246["implementation_commit"] != evidence["implementation_commit"]:
    raise SystemExit("AION-246 implementation commit/evidence mismatch")
if aion246["evidence_report_fingerprint"] != evidence["report_fingerprint"]:
    raise SystemExit("AION-246 evidence fingerprint mismatch")
if "PENDING_AION_246" in json.dumps(aion246, sort_keys=True):
    raise SystemExit("AION-246 record contains unreconciled placeholder")

for pyproject in (
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/pyproject.toml",
):
    payload = tomllib.loads((ROOT / pyproject).read_text(encoding="utf-8"))
    if payload["project"]["version"] != EXPECTED_VERSION:
        raise SystemExit(f"development package version mismatch: {pyproject}")

service = ControlledExternalCognitionService()
providers = service.load_provider_manifests()
models = service.load_model_manifests()
capabilities = service.load_capability_records()
if (len(providers), len(models), len(capabilities)) != (3, 6, 18):
    raise SystemExit("default manifest counts changed")
if len(default_route_policies()) != 6:
    raise SystemExit("default route policy count changed")
if len(default_structured_output_schemas()) != 2:
    raise SystemExit("structured output schema count changed")
if len(default_budgets()) != 6:
    raise SystemExit("default budget tuple changed")

for key, value in {
    "actual_provider_calls": 0,
    "public_network_calls": 0,
    "external_network_egress_calls": 0,
    "dns_resolutions": 0,
    "provider_credentials_read": 0,
    "provider_tokens_read": 0,
    "persistent_memory_writes": 0,
    "external_tool_executions": 0,
    "external_connector_calls": 0,
    "git_operations": 0,
    "source_mutations": 0,
    "production_deployments": 0,
    "model_weight_changes": 0,
}.items():
    if hold.get(key) != value:
        raise SystemExit(f"runtime hold zero counter mismatch: {key}")

print("controlled external cognition gateway foundation PASS")
PY
