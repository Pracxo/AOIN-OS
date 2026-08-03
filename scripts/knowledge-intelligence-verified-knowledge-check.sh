#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"
export PYTHONPATH="$ROOT_DIR/services/brain-api/src:$ROOT_DIR/scripts/lib:${PYTHONPATH:-}"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_VERIFIED_KNOWLEDGE_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-verified-knowledge-no-go-regression.sh
./scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh
./scripts/knowledge-intelligence-verified-knowledge-authorization-check.sh

required_sources=(
  services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py
  services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py
  services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py
  services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py
  services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py
)
for path in "${required_sources[@]}"; do
  [[ -f "$path" ]] || { echo "ERROR: required AION-217 source missing: $path" >&2; exit 1; }
done

json_files=(
  examples/knowledge-intelligence/engagement-learning-candidate-batch.json
  examples/knowledge-intelligence/engagement-learning-candidate.json
  examples/knowledge-intelligence/engagement-signal-batch.json
  examples/knowledge-intelligence/engagement-signal-metadata.json
  examples/knowledge-intelligence/engagement-signal.json
  examples/knowledge-intelligence/integrated-knowledge-lineage-v1.json
  examples/knowledge-intelligence/verified-knowledge-authorization.json
  examples/knowledge-intelligence/verified-knowledge-candidate-batch.json
  examples/knowledge-intelligence/verified-knowledge-candidate-history.json
  examples/knowledge-intelligence/verified-knowledge-candidate-integrity-report.json
  examples/knowledge-intelligence/verified-knowledge-candidate-query.json
  examples/knowledge-intelligence/verified-knowledge-candidate-version.json
  examples/knowledge-intelligence/verified-knowledge-candidate.json
  examples/knowledge-intelligence/verified-knowledge-eligibility-decision.json
  examples/knowledge-intelligence/verified-knowledge-eligibility-input.json
  examples/knowledge-intelligence/verified-knowledge-evidence-bundle.json
  examples/knowledge-intelligence/verified-knowledge-integrity-report.json
  examples/knowledge-intelligence/verified-knowledge-memory-snapshot.json
  examples/knowledge-intelligence/verified-knowledge-operator-review-item.json
  examples/knowledge-intelligence/verified-knowledge-query-result.json
  examples/knowledge-intelligence/verified-knowledge-query.json
  examples/knowledge-intelligence/verified-knowledge-refutation-candidate.json
  examples/knowledge-intelligence/verified-knowledge-resource-budget.json
  examples/knowledge-intelligence/verified-knowledge-revalidation-request.json
  examples/knowledge-intelligence/verified-knowledge-revalidation-result.json
  examples/knowledge-intelligence/verified-knowledge-runtime-hold.json
  examples/knowledge-intelligence/verified-knowledge-support-candidate.json
  operator-console-static/demo-data/knowledge-intelligence-engagement-learning-candidate.json
  operator-console-static/demo-data/knowledge-intelligence-engagement-learning-candidates.json
  operator-console-static/demo-data/knowledge-intelligence-engagement-signals.json
  operator-console-static/demo-data/knowledge-intelligence-verified-candidate-integrity.json
  operator-console-static/demo-data/knowledge-intelligence-verified-candidate-refutation.json
  operator-console-static/demo-data/knowledge-intelligence-verified-candidate-revalidation.json
  operator-console-static/demo-data/knowledge-intelligence-verified-candidate-support.json
  operator-console-static/demo-data/knowledge-intelligence-verified-candidate-versioning.json
  operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-authorization.json
  operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-candidate.json
  operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-runtime-hold.json
  operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-versioning.json
  operator-console-static/demo-data/knowledge-intelligence-verified-memory-runtime-hold.json
  operator-console-static/demo-data/knowledge-intelligence-verified-memory.json
)
for path in "${json_files[@]}"; do
  "$PYTHON_BIN" -m json.tool "$path" >/dev/null
done

docs_files=(
  docs/adr/0181-deterministic-verified-knowledge-candidate-memory-and-engagement-learning-candidate-plane.md
  docs/knowledge-intelligence/aion-217-checklist.md
  docs/knowledge-intelligence/engagement-learning-implementation.md
  docs/knowledge-intelligence/engagement-learning-operator-review.md
  docs/knowledge-intelligence/engagement-learning-versioning.md
  docs/knowledge-intelligence/engagement-signal-contracts.md
  docs/knowledge-intelligence/engagement-signal-non-factual-policy.md
  docs/knowledge-intelligence/integrated-knowledge-lineage-implementation.md
  docs/knowledge-intelligence/verified-knowledge-candidate-eligibility.md
  docs/knowledge-intelligence/verified-knowledge-candidate-history.md
  docs/knowledge-intelligence/verified-knowledge-candidate-kinds.md
  docs/knowledge-intelligence/verified-knowledge-candidate-versioning.md
  docs/knowledge-intelligence/verified-knowledge-confidence-inheritance.md
  docs/knowledge-intelligence/verified-knowledge-confidence-non-amplification.md
  docs/knowledge-intelligence/verified-knowledge-contracts.md
  docs/knowledge-intelligence/verified-knowledge-fixture-replay.md
  docs/knowledge-intelligence/verified-knowledge-implementation.md
  docs/knowledge-intelligence/verified-knowledge-integrity.md
  docs/knowledge-intelligence/verified-knowledge-memory-repository.md
  docs/knowledge-intelligence/verified-knowledge-memory-snapshots.md
  docs/knowledge-intelligence/verified-knowledge-operator-runbook.md
  docs/knowledge-intelligence/verified-knowledge-query-model.md
  docs/knowledge-intelligence/verified-knowledge-revalidation-implementation.md
  docs/knowledge-intelligence/verified-knowledge-security-review.md
  docs/release/knowledge-intelligence-verified-knowledge-implementation.md
  docs/release/knowledge-intelligence-verified-knowledge-security-evidence.md
)
for path in "${docs_files[@]}"; do
  [[ -s "$path" ]] || { echo "ERROR: required AION-217 doc missing: $path" >&2; exit 1; }
done
rg -n "0181-deterministic-verified-knowledge-candidate-memory" docs/adr/README.md >/dev/null

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
from pathlib import Path

import knowledge_intelligence_verified_knowledge_authorization as auth
from aion_brain.contracts.knowledge_verified_memory import (
    EngagementLearningCandidateKind,
    VerifiedKnowledgeCandidateKind,
    VerifiedKnowledgeResourceBudget,
)

ROOT = Path(os.environ["AION_REPO_ROOT"])

auth.validate_authorization_files(ROOT)
auth.validate_runtime_hold(ROOT)

budget = VerifiedKnowledgeResourceBudget()
zero_budget_fields = (
    "maximum_persistent_verified_knowledge_write_batch",
    "maximum_automatic_knowledge_promotions",
    "maximum_operator_approval_creations",
    "maximum_cognitive_memory_writes",
    "maximum_belief_mutations",
    "maximum_engagement_fact_promotions",
    "maximum_engagement_confidence_effects",
    "maximum_public_network_calls",
    "maximum_dns_resolutions",
    "maximum_search_provider_calls",
    "maximum_connector_calls",
    "maximum_model_provider_calls",
    "maximum_actual_tool_executions",
    "maximum_shell_commands",
    "maximum_subprocess_executions",
    "maximum_browser_actions",
    "maximum_filesystem_mutations",
    "maximum_source_mutations",
    "maximum_git_operations",
    "maximum_runtime_created_pull_requests",
    "maximum_approvals_created",
    "maximum_deployments",
    "maximum_model_weight_changes",
)
for field in zero_budget_fields:
    if getattr(budget, field) != 0:
        raise SystemExit(f"resource budget must remain zero: {field}")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
authorization = json.loads(
    (ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text()
)
for label, payload in {"program": program, "authorization": authorization}.items():
    final_state = auth.is_final_public_pilot_state(payload)
    expected_authorization = (
        auth.NEXT_AUTHORIZATION_ID if final_state else auth.AUTHORIZATION_ID
    )
    expected_closeout = auth.NEXT_FORMAL_CLOSEOUT_TASK if final_state else auth.FORMAL_CLOSEOUT_TASK
    if payload["authorization_transaction_id"] != expected_authorization:
        raise SystemExit(f"{label} active authorization mismatch")
    if payload["formal_closeout_task"] != expected_closeout:
        raise SystemExit(f"{label} formal closeout mismatch")
    if payload["program_state"] not in {auth.IMPLEMENTED_PROGRAM_STATE, auth.FINAL_PROGRAM_STATE}:
        raise SystemExit(f"{label} implemented program state mismatch")
    for key in (
        "verified_knowledge_runtime_enabled",
        "persistent_verified_knowledge_write_enabled",
        "automatic_verified_knowledge_promotion_enabled",
        "cognitive_memory_write_enabled",
        "belief_mutation_enabled",
        "engagement_signal_as_fact_enabled",
        "engagement_confidence_effect_enabled",
        "public_network_fetch_enabled",
        "actual_tool_execution_enabled",
        "runtime_effect",
    ):
        if payload.get(key) is not False:
            raise SystemExit(f"{label} runtime boundary enabled: {key}")

support = json.loads(
    (ROOT / "examples/knowledge-intelligence/verified-knowledge-support-candidate.json")
    .read_text()
)
refutation = json.loads(
    (ROOT / "examples/knowledge-intelligence/verified-knowledge-refutation-candidate.json")
    .read_text()
)
if support["candidate_kind"] != VerifiedKnowledgeCandidateKind.SUPPORT_CANDIDATE.value:
    raise SystemExit("support candidate kind mismatch")
if refutation["candidate_kind"] != VerifiedKnowledgeCandidateKind.REFUTATION_CANDIDATE.value:
    raise SystemExit("refutation candidate kind mismatch")
if support["automatic_promotion"] is not False or refutation["automatic_promotion"] is not False:
    raise SystemExit("candidate automatic promotion must remain false")
if support["candidate_confidence_cap"] > support["assessment_confidence"]:
    raise SystemExit("support candidate confidence amplification detected")

engagement_batch = json.loads(
    (ROOT / "examples/knowledge-intelligence/engagement-learning-candidate-batch.json")
    .read_text()
)
expected_engagement_kinds = {kind.value for kind in EngagementLearningCandidateKind}
actual_engagement_kinds = {
    item["candidate_kind"] for item in engagement_batch["candidates"]
}
if actual_engagement_kinds != expected_engagement_kinds:
    raise SystemExit("engagement learning candidate coverage mismatch")
if any(item.get("factual_effect") is not False for item in engagement_batch["candidates"]):
    raise SystemExit("engagement candidate factual effect detected")
if any(item.get("automatic_application") is not False for item in engagement_batch["candidates"]):
    raise SystemExit("engagement candidate automatic application detected")

revalidation = json.loads(
    (ROOT / "examples/knowledge-intelligence/verified-knowledge-revalidation-result.json")
    .read_text()
)
request = revalidation.get("request", {})
if request.get("operator_invoked") is not True:
    raise SystemExit("revalidation must remain explicit")
if "operator_requested" not in request.get("triggers", []):
    raise SystemExit("operator revalidation trigger missing")
if request.get("scheduler_invoked") is not False:
    raise SystemExit("scheduled revalidation must remain disabled")
if request.get("background_worker_invoked") is not False:
    raise SystemExit("background revalidation worker must remain disabled")
for key in ("persistent_write_applied", "approval_created", "runtime_effect"):
    if revalidation.get(key) is not False:
        raise SystemExit(f"revalidation result boundary enabled: {key}")
PY

if is_nested_gate_context; then
  echo "PASS: focused AION-217 pytest deferred to outer gate"
else
  AION_VERIFIED_KNOWLEDGE_CHECK_RUNNING=1 "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_knowledge_verified_memory_*.py \
    services/brain-api/tests/test_knowledge_engagement_*.py \
    services/brain-api/tests/test_knowledge_intelligence_aion216_delivery_reconciliation.py \
    services/brain-api/tests/test_knowledge_intelligence_task_catalog_consistency.py \
    services/brain-api/tests/test_knowledge_intelligence_project_status_consistency.py \
    -q
fi

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/knowledge-intelligence-integrated-research-agent-operator-evaluation-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
./scripts/repo-health.sh

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence verified knowledge memory PASS"
