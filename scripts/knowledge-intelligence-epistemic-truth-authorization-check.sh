#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"
export AION_REPO_ROOT="$ROOT_DIR"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-epistemic-truth-authorization-no-go-regression.sh

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-truth-authorization.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-scorecard.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-resource-budget.json >/dev/null
"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/epistemic-runtime-hold.json >/dev/null

"$PYTHON_BIN" - <<'PYSCRIPT'

from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
DECISION = "TEMPORAL_CLAIM_EVIDENCE_GRAPH_OPERATOR_EVALUATION_PASS_RECOMMEND_EPISTEMIC_TRUTH_ENGINE_AUTHORIZATION"
CLAIM_AUTH = "AION-208-KI-0003"
NEXT_AUTH = "AION-210-KI-0004"
AION209_FEATURES = [
    "0a84080c83f87eef94b5191c432021776c6a336a",
    "d50252c84a0a02b75317c7d2051eaee4fb9dc54c",
]
AION209_MERGE = "f9e2438a49aae458983fc57cee5c12b5ef0ab856"
SCOPE = "deterministic-evidence-corroboration-contradiction-freshness-source-independence-confidence-assessment-core"
RESOURCE_LIMITS = {
    "maximum_claims_per_assessment_batch": 500,
    "maximum_evidence_bindings_per_claim": 100,
    "maximum_source_registry_references_per_claim": 50,
    "maximum_citation_references_per_claim": 50,
    "maximum_lineage_groups_per_claim": 20,
    "maximum_relation_edges_per_claim": 100,
    "maximum_reason_codes_per_assessment": 50,
    "maximum_operator_review_items": 500,
    "maximum_epistemic_assessments": 500,
    "maximum_confidence_calculations": 500,
    "maximum_benchmark_cases": 1000,
    "maximum_query_results": 1000,
    "maximum_fixture_records": 5000,
    "maximum_fixture_bytes": 4194304,
    "maximum_concurrent_assessments": 4,
    "maximum_persistent_assessment_write_batch": 0,
    "maximum_source_body_bytes": 0,
    "maximum_automatic_claim_extractions": 0,
    "maximum_absolute_truth_decisions": 0,
    "maximum_automatic_claim_acceptances": 0,
    "maximum_automatic_claim_rejections": 0,
    "maximum_contradiction_resolutions": 0,
    "maximum_knowledge_promotions": 0,
    "maximum_belief_mutations": 0,
    "maximum_network_calls": 0,
    "maximum_search_provider_calls": 0,
    "maximum_connector_calls": 0,
    "maximum_model_provider_calls": 0,
    "maximum_source_mutations": 0,
    "maximum_git_operations": 0,
    "maximum_runtime_created_pull_requests": 0,
    "maximum_approvals_created": 0,
    "maximum_deployments": 0,
    "maximum_model_weight_changes": 0,
}
AION211_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
PROHIBITED_NAMES = {
    "package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb",
    "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock",
}
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {"README.md", "AGENTS.md"}


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base:
        entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip())
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def load_json(relative: str) -> dict:
    return json.loads((ROOT / relative).read_text())


def assert_no_prohibited_paths() -> None:
    for parts in changed_entries():
        status, paths = parts[0], parts[1:]
        if status.startswith(("D", "R")):
            raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
        for path in paths:
            normalized = path.replace("\\", "/")
            if Path(normalized).name in PROHIBITED_NAMES:
                raise SystemExit(f"dependency/package file changed: {normalized}")
            if normalized in AION211_SOURCE:
                raise SystemExit(f"AION-211 source is prohibited on AION-210: {normalized}")
            if normalized.startswith(PROHIBITED_PREFIXES):
                raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
            if normalized not in ALLOWED_EXACT and not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
                raise SystemExit(f"path outside AION-210 scope: {normalized}")
    for relative in AION211_SOURCE:
        if (ROOT / relative).exists():
            raise SystemExit(f"AION-211 source exists before authorization implementation task: {relative}")


def assert_release_state() -> None:
    if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
        raise SystemExit("aion-v0.1.0 tag moved")
    if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
        raise SystemExit("v0.2 tag exists")


def assert_report() -> dict:
    report = load_json("examples/knowledge-intelligence/claim-graph-operator-evaluation-report.json")
    assert report["evaluation_id"] == "AION-TCGE-001"
    assert report["evaluation_type"] == "read_only_temporal_claim_evidence_graph_operator_evaluation"
    assert report["program_id"] == "AION-KNOWLEDGE-INTELLIGENCE-001"
    assert report["implementation_task"] == "AION-209"
    assert report["closeout_task"] == "AION-210"
    assert report["implementation_prs"] == [121]
    assert report["implementation_feature_commits"] == AION209_FEATURES
    assert report["implementation_merge_commits"] == [AION209_MERGE]
    assert report["decision"] == DECISION
    assert report["evaluation_passed"] is True
    assert report["scenario_count"] == 28
    assert len(report["scenario_results"]) == 28
    assert all(item["passed"] is True for item in report["scenario_results"])
    assert all(item["passed"] is True for item in report["hard_gate_results"])
    for key, value in report["repository_integrity"].items():
        if isinstance(value, bool):
            continue
        assert value == 0, key
    assert report["repository_integrity"]["repository_unchanged"] is True
    for key, value in report["runtime_state"].items():
        assert value is False, key
    return report


def assert_ledgers() -> tuple[dict, dict, dict, dict]:
    program = load_json("docs/knowledge-intelligence/program-ledger.json")
    auth = load_json("docs/knowledge-intelligence/authorization-ledger.json")
    records = auth["records"]
    active = [record for record in records if record.get("authorization_active") is True]
    assert len(active) == 1
    active_record = active[0]
    closed = [record for record in records if record.get("authorization_transaction_id") == CLAIM_AUTH]
    assert len(closed) == 1
    closed_record = closed[0]
    assert closed_record["authorization_active"] is False
    assert closed_record["authorization_consumed"] is True
    assert closed_record["authorization_consumed_by_task"] == "AION-209"
    assert closed_record["authorization_consumed_by_prs"] == [121]
    assert closed_record["authorization_consumed_by_feature_commits"] == AION209_FEATURES
    assert closed_record["authorization_consumed_by_merge_commits"] == [AION209_MERGE]
    assert closed_record["authorization_expired"] is True
    assert closed_record["authorization_reusable"] is False
    assert closed_record["authorization_closed_by_task"] == "AION-210"
    assert closed_record["claim_graph_operator_evaluation_id"] == "AION-TCGE-001"
    assert closed_record["claim_graph_operator_evaluation_decision"] == DECISION
    assert closed_record["evaluation_used_as_approval"] is False
    assert active_record["authorization_transaction_id"] == NEXT_AUTH
    assert active_record["approval_record_id"] == NEXT_AUTH
    assert active_record["parent_authorization_transaction_id"] == CLAIM_AUTH
    assert active_record["parent_evaluation_id"] == "AION-TCGE-001"
    assert active_record["parent_evaluation_decision"] == DECISION
    assert active_record["implementation_task"] == "AION-211"
    assert active_record["formal_closeout_task"] == "AION-212"
    assert active_record["authorization_scope"] == SCOPE
    assert active_record["authorization_transaction_approved"] is True
    assert active_record["explicit_approval_record_approval"] is True
    assert active_record["implementation_authorization_approved"] is True
    assert active_record["implementation_go_status"] is True
    assert active_record["implementation_no_go_status"] is False
    assert active_record["authorization_consumed"] is False
    assert active_record["authorization_expired"] is False
    assert active_record["authorization_reusable"] is False
    assert all(active_record["authorized_capabilities"].values())
    assert all(value is False for value in active_record["prohibited_capabilities"].values())
    assert active_record["resource_limits"] == RESOURCE_LIMITS
    assert program["program_state"] == "epistemic_truth_engine_authorized_not_implemented"
    assert program["claim_graph_operator_evaluation_passed"] is True
    assert program["active_knowledge_implementation_authorization_count"] == 1
    assert program["active_knowledge_implementation_authorization"] == NEXT_AUTH
    assert program["active_knowledge_implementation_task"] == "AION-211"
    assert program["formal_closeout_task"] == "AION-212"
    assert program["epistemic_truth_engine_authorized"] is True
    assert program["epistemic_truth_engine_implemented"] is False
    for key in (
        "claim_graph_runtime_enabled", "persistent_claim_graph_write_enabled", "automatic_claim_extraction_enabled",
        "claim_verification_enabled", "truth_decision_enabled", "epistemic_confidence_enabled",
        "contradiction_resolution_enabled", "knowledge_promotion_enabled", "belief_mutation_enabled",
        "network_access_enabled", "absolute_truth_oracle_enabled", "runtime_effect",
    ):
        assert program.get(key, False) is False, key
        assert active_record.get(key, False) is False, key
    return program, auth, closed_record, active_record


def assert_all() -> None:
    assert_no_prohibited_paths()
    assert_release_state()
    assert_report()
    assert_ledgers()

assert_all()
auth = load_json("examples/knowledge-intelligence/epistemic-truth-authorization.json")
scorecard = load_json("examples/knowledge-intelligence/epistemic-scorecard.json")
budget = load_json("examples/knowledge-intelligence/epistemic-resource-budget.json")
runtime = load_json("examples/knowledge-intelligence/epistemic-runtime-hold.json")
assert auth["authorization_transaction_id"] == NEXT_AUTH
assert auth["implementation_task"] == "AION-211"
assert auth["formal_closeout_task"] == "AION-212"
assert auth["authorization_scope"] == SCOPE
assert all(auth["authorized_capabilities"].values())
assert all(value is False for value in auth["prohibited_capabilities"].values())
assert auth["resource_limits"] == RESOURCE_LIMITS
assert scorecard["model_call_enabled"] is False
assert scorecard["hidden_weights_enabled"] is False
assert scorecard["learned_weights_enabled"] is False
assert scorecard["explicit_abstention_required"] is True
assert budget["resource_limits"] == RESOURCE_LIMITS
assert runtime["epistemic_truth_engine_implemented"] is False
assert runtime["runtime_enabled"] is False
PYSCRIPT

if is_nested_gate_context; then
  echo "PASS: focused epistemic truth pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest     services/brain-api/tests/test_knowledge_epistemic_truth_authorization_docs.py     services/brain-api/tests/test_knowledge_epistemic_truth_authorization_validator.py     services/brain-api/tests/test_knowledge_epistemic_truth_scope_spec.py     services/brain-api/tests/test_knowledge_epistemic_truth_budget_spec.py     services/brain-api/tests/test_knowledge_epistemic_truth_scorecard_spec.py     services/brain-api/tests/test_knowledge_epistemic_truth_threat_model.py     -q
fi

echo "knowledge intelligence epistemic truth authorization PASS"
