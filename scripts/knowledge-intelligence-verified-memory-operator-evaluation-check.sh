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

./scripts/knowledge-intelligence-verified-memory-operator-evaluation-no-go-regression.sh

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

root = Path(__import__("os").environ["AION_REPO_ROOT"])
report_path = root / "examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json"
if not report_path.exists():
    print("knowledge intelligence verified memory operator evaluation check skeleton PASS")
    raise SystemExit(0)

report = json.loads(report_path.read_text(encoding="utf-8"))
required_scenarios = [
    "valid_support_candidate",
    "valid_refutation_candidate",
    "integrated_lineage_integrity",
    "candidate_confidence_non_amplification",
    "source_independence_minimum",
    "coverage_and_provenance_requirements",
    "stale_evidence_blocking",
    "retraction_blocking",
    "supersession_policy",
    "scope_mismatch_blocking",
    "unresolved_contradiction_blocking",
    "material_dissent_blocking",
    "tool_evidence_non_factual_boundary",
    "upstream_abstention",
    "candidate_identity_and_version_boundary",
    "version_idempotency_and_collision",
    "supersession_history_preservation",
    "retraction_expiry_and_archive_history",
    "explicit_revalidation",
    "copy_on_write_repository",
    "snapshots_and_queries",
    "fixture_path_schema_and_redaction",
    "engagement_signal_non_factual",
    "engagement_learning_candidate_mapping",
    "engagement_cannot_change_candidate_state",
    "resource_budgets_and_zero_persistence",
    "determinism_concurrency_and_performance",
    "no_runtime_network_promotion_memory_belief_or_repository_effect",
]
assert report["evaluation_id"] == "AION-VKME-001"
assert report["scenario_count"] == 28
assert [item["scenario_id"] for item in report["scenario_results"]] == required_scenarios
assert all(item["executed"] and item["passed"] for item in report["scenario_results"])
assert all(report["hard_gate_results"].values())
for key in (
    "public_network_requests",
    "dns_resolutions",
    "search_provider_calls",
    "connector_calls",
    "model_provider_calls",
    "actual_tool_executions",
    "shell_executions",
    "subprocess_executions",
    "browser_actions",
    "filesystem_mutations",
    "source_mutations",
    "git_operations",
    "runtime_pull_requests",
    "runtime_approvals",
    "deployments",
    "model_weight_changes",
    "persistent_verified_knowledge_writes",
    "automatic_knowledge_promotions",
    "cognitive_memory_writes",
    "belief_mutations",
    "engagement_fact_promotions",
    "engagement_confidence_effects",
):
    assert report[key] == 0, key
assert report["repository_unchanged"] is True
assert report["synthetic"] is True
assert report["read_only"] is True
assert report["redacted"] is True
if report["evaluation_passed"]:
    assert report["decision"] == (
        "VERIFIED_KNOWLEDGE_MEMORY_OPERATOR_EVALUATION_PASS_RECOMMEND_CONTROLLED_"
        "PUBLIC_RESEARCH_PILOT_AUTHORIZATION"
    )
else:
    assert report["decision"] == "VERIFIED_KNOWLEDGE_MEMORY_OPERATOR_EVALUATION_FAIL_REMAIN_DISABLED"
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if [[ -f examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json ]] &&
  "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import json
from pathlib import Path
report = json.loads(Path("examples/knowledge-intelligence/verified-memory-operator-evaluation-report.json").read_text())
raise SystemExit(0 if report.get("evaluation_passed") is False else 1)
PY
then
  echo "knowledge intelligence verified memory operator evaluation FAIL RECORDED"
else
  echo "knowledge intelligence verified memory operator evaluation PASS"
fi
