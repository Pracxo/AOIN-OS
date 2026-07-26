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

if [[ "${AION_INTEGRATED_RESEARCH_AGENT_EVALUATION_RUNNING:-}" == "1" ]]; then
  aion_confirm_immutable_v01_tag_history >/dev/null
  echo "PASS: inherited branch-diff no-go deferred to AION-216 aggregate scope"
  exit 0
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
POST_AION210_CONTEXT = os.environ.get("AION_KNOWLEDGE_POST_AION210_CONTEXT") == "1"
PROGRAM_PATH = ROOT / "docs/knowledge-intelligence/program-ledger.json"
TOOL_VERIFICATION_IMPLEMENTED_STATE = (
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"
)
VERIFIED_KNOWLEDGE_AUTHORIZED_STATE = "verified_knowledge_memory_authorized_not_implemented"
VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
CURRENT_PROGRAM_STATE = ""
if PROGRAM_PATH.exists():
    try:
        CURRENT_PROGRAM_STATE = json.loads(PROGRAM_PATH.read_text()).get("program_state", "")
        POST_AION210_CONTEXT = (
            POST_AION210_CONTEXT
            or CURRENT_PROGRAM_STATE
            in {
                "epistemic_truth_engine_authorized_not_implemented",
                "epistemic_truth_engine_implemented_persistent_write_disabled_pending_closeout",
                "domain_expert_mesh_authorized_not_implemented",
                "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
                "tool_verification_fabric_authorized_not_implemented",
                TOOL_VERIFICATION_IMPLEMENTED_STATE,
                VERIFIED_KNOWLEDGE_AUTHORIZED_STATE,
                VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE,
            }
        )
    except json.JSONDecodeError:
        pass
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/visual-brain.md",
    "docs/knowledge-intelligence/program-charter.md",
    "docs/knowledge-intelligence/architecture-roadmap.md",
    "docs/knowledge-intelligence/security-boundary.md",
    "docs/knowledge-intelligence/operator-model.md",
    "docs/knowledge-intelligence/program-ledger.json",
    "docs/knowledge-intelligence/authorization-ledger.json",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-architecture.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-boundary.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-data-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-relations.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-time-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-jurisdiction-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-version-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-resource-budgets.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-threat-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-roadmap.md",
    "docs/release/knowledge-intelligence-claim-graph-authorization-transaction.md",
    "docs/release/knowledge-intelligence-claim-graph-scope.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/adr/README.md",
    "operator-console-static/index.html",
    "operator-console-static/app.js",
    "operator-console-static/README.md",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
}
ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/claim-",
    "docs/knowledge-intelligence/structural-conflict-candidates.md",
    "docs/knowledge-intelligence/aion-209-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-",
    "docs/adr/0173-immutable-temporal-claim-evidence-graph-core.md",
    "examples/knowledge-intelligence/",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph",
    "services/brain-api/tests/test_knowledge_claim_graph",
)
ALLOWED_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
}
ALLOWED_SCRIPTS = {
    "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
    "scripts/knowledge-intelligence-claim-graph-check.sh",
    "scripts/knowledge-intelligence-claim-graph-no-go-regression.sh",
    "scripts/cognitive-local-offline-pilot-closeout-check.sh",
    "scripts/auth-design-check.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/operator-action-write-path-no-go-regression.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/production-auth-architecture-check.sh",
    "scripts/production-auth-core-check.sh",
    "scripts/production-auth-core-no-go-regression.sh",
    "scripts/production-auth-core-stabilization-check.sh",
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
}
ALLOWED_TESTS = {
    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py",
    "services/brain-api/tests/test_knowledge_research_authorization_closeout.py",
    "services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py",
}
POST_AION210_ALLOWED_EXACT = {
    "docs/adr/0174-temporal-claim-evidence-graph-evaluation-and-epistemic-truth-engine-authorization.md",
    "docs/adr/0175-deterministic-epistemic-evidence-assessment-engine-core.md",
    "docs/knowledge-intelligence/aion-211-checklist.md",
    "docs/knowledge-intelligence/aion-213-checklist.md",
    "docs/knowledge-intelligence/computational-expert-profiles.md",
    "examples/knowledge-intelligence/claim-epistemic-assessment.json",
    "examples/knowledge-intelligence/evidence-contribution.json",
    "examples/knowledge-intelligence/role-evidence-score.json",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-plane-check.sh",
    "scripts/knowledge-intelligence-research-plane-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-check.sh",
    "scripts/knowledge-intelligence-source-registry-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-runtime-hold.sh",
    "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-epistemic-assessment-check.sh",
    "scripts/knowledge-intelligence-epistemic-assessment-no-go-regression.sh",
    "scripts/static-console-safety-check.sh",
    "scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py",
    "services/brain-api/tests/knowledge_source_registry_test_helpers.py",
    "services/brain-api/tests/knowledge_claim_graph_evaluation_test_helpers.py",
    "services/brain-api/tests/knowledge_domain_expert_mesh_test_helpers.py",
    "services/brain-api/tests/test_knowledge_source_registry_authorization_closeout.py",
    "services/brain-api/tests/test_self_improvement_postmerge_evidence_reconciliation.py",
    "services/brain-api/tests/test_knowledge_claim_graph_authorization_closeout.py",
    "services/brain-api/tests/test_knowledge_claim_graph_operator_evaluation.py",
    "services/brain-api/tests/test_knowledge_claim_graph_operator_evaluation_docs.py",
    "services/brain-api/tests/test_knowledge_claim_graph_evaluation_no_side_effects.py",
    "services/brain-api/tests/test_knowledge_claim_graph_evaluation_repository_integrity.py",
    "services/brain-api/tests/test_knowledge_intelligence_current_projection.py",
}
POST_AION210_ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/claim-graph-evaluation",
    "docs/knowledge-intelligence/claim-graph-operator-evaluation",
    "docs/knowledge-intelligence/epistemic-",
    "docs/release/knowledge-intelligence-claim-graph-evaluation-",
    "docs/release/knowledge-intelligence-epistemic-assessment-",
    "docs/release/knowledge-intelligence-epistemic-truth-",
    "examples/knowledge-intelligence/claim-graph-evaluation",
    "examples/knowledge-intelligence/claim-graph-operator-evaluation",
    "examples/knowledge-intelligence/epistemic-",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph-evaluation",
    "operator-console-static/demo-data/knowledge-intelligence-epistemic-",
    "scripts/knowledge-intelligence-claim-graph-operator-evaluation-",
    "scripts/knowledge-intelligence-epistemic-assessment-",
    "scripts/knowledge-intelligence-epistemic-truth-",
    "scripts/knowledge-intelligence-domain-expert-mesh-",
    "scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py",
    "scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py",
    "scripts/lib/v02_production_auth_authorization.py",
    "docs/knowledge-intelligence/epistemic-assessment-operator-evaluation",
    "docs/knowledge-intelligence/epistemic-assessment-evaluation",
    "docs/knowledge-intelligence/domain-expert-",
    "docs/knowledge-intelligence/domain-expert-mesh",
    "docs/knowledge-intelligence/domain-taxonomy",
    "docs/release/knowledge-intelligence-epistemic-assessment-evaluation",
    "docs/release/knowledge-intelligence-domain-expert-mesh",
    "docs/adr/0176-epistemic-assessment-evaluation-and-domain-expert-mesh-authorization.md",
    "docs/adr/0177-deterministic-domain-expert-mesh-core.md",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-",
    "examples/knowledge-intelligence/domain-expert-",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_",
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/tests/test_knowledge_epistemic_assessment_",
    "services/brain-api/tests/test_knowledge_epistemic_truth_",
    "services/brain-api/tests/test_knowledge_domain_expert_mesh_",
)
AION214_ALLOWED_EXACT = {
    "docs/adr/0178-domain-expert-mesh-evaluation-and-tool-verification-authorization.md",
    "operator-console-static/demo-data/knowledge-intelligence-program.json",
    "scripts/lib/knowledge_intelligence_domain_expert_mesh_operator_evaluation.py",
    "scripts/lib/knowledge_intelligence_tool_verification_authorization.py",
}
AION215_ALLOWED_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_attestation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_effects.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_manifests.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_planning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_simulation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/tool_verification_fabric.py",
}
AION217_ALLOWED_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py",
}
AION217_ALLOWED_EXACT = {
    "scripts/connector-platform-freeze-check.sh",
    "services/brain-api/tests/test_self_improvement_postmerge_evidence_reconciliation.py",
    "services/brain-api/tests/test_self_improvement_shadow_activation_authorization_docs.py",
    "services/brain-api/tests/test_self_improvement_shadow_activation_evaluation_repository_integrity.py",
    "services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py",
}
AION214_ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/domain-expert-mesh-operator-evaluation",
    "docs/knowledge-intelligence/domain-expert-mesh-evaluation",
    "docs/knowledge-intelligence/tool-",
    "docs/release/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "docs/release/knowledge-intelligence-tool-verification",
    "examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation",
    "examples/knowledge-intelligence/tool-",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "operator-console-static/demo-data/knowledge-intelligence-tool-",
    "scripts/knowledge-intelligence-domain-expert-mesh-operator-evaluation",
    "scripts/knowledge-intelligence-tool-verification",
    "services/brain-api/tests/test_knowledge_domain_expert_mesh_operator_evaluation",
    "services/brain-api/tests/test_knowledge_tool_verification",
)
AION216_ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "operator-console-static/index.html",
    "operator-console-static/app.js",
    "operator-console-static/README.md",
}
AION216_ALLOWED_PREFIXES = (
    "docs/",
    "examples/knowledge-intelligence/",
    "operator-console-static/demo-data/knowledge-intelligence-",
    "scripts/knowledge-intelligence-",
    "scripts/lib/knowledge_intelligence_",
    "services/brain-api/tests/knowledge_",
    "services/brain-api/tests/test_knowledge_",
)
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/api_support/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
    "services/brain-api/src/aion_brain/kernel/",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/security/",
    "services/brain-api/src/aion_brain/self_improvement/",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_",
    "services/brain-api/src/aion_brain/contracts/knowledge_research.py",
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
PROHIBITED_NAMES = {
    "package.json",
    "package-lock.json",
    "pnpm-lock.yaml",
    "yarn.lock",
    "bun.lockb",
    "poetry.lock",
    "uv.lock",
    "Pipfile",
    "Pipfile.lock",
}


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
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    entries.extend(
        line.split("\t")
        for line in run(["git", "diff", "--name-status"]).stdout.splitlines()
        if line.strip()
    )
    entries.extend(
        line.split("\t")
        for line in run(["git", "diff", "--cached", "--name-status"]).stdout.splitlines()
        if line.strip()
    )
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


def path_allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if POST_AION210_CONTEXT and (
        normalized in POST_AION210_ALLOWED_EXACT
        or any(normalized.startswith(prefix) for prefix in POST_AION210_ALLOWED_PREFIXES)
        or normalized in AION214_ALLOWED_EXACT
        or any(normalized.startswith(prefix) for prefix in AION214_ALLOWED_PREFIXES)
    ):
        return True
    if (
        CURRENT_PROGRAM_STATE == TOOL_VERIFICATION_IMPLEMENTED_STATE
        and normalized in AION215_ALLOWED_SOURCE
    ):
        return True
    if CURRENT_PROGRAM_STATE == VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE and (
        normalized in AION217_ALLOWED_EXACT or normalized in AION217_ALLOWED_SOURCE
    ):
        return True
    if CURRENT_PROGRAM_STATE in {
        VERIFIED_KNOWLEDGE_AUTHORIZED_STATE,
        VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE,
    } and (
        normalized in AION216_ALLOWED_EXACT
        or any(normalized.startswith(prefix) for prefix in AION216_ALLOWED_PREFIXES)
    ):
        return True
    if (
        normalized in ALLOWED_EXACT
        or normalized in ALLOWED_SOURCE
        or normalized in ALLOWED_SCRIPTS
        or normalized in ALLOWED_TESTS
    ):
        return True
    return any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES)


for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if any(normalized.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            if normalized not in ALLOWED_SOURCE and normalized not in ALLOWED_EXACT:
                raise SystemExit(f"prohibited runtime/workflow/dependency path changed: {normalized}")
        if not path_allowed(normalized):
            raise SystemExit(f"path outside AION-209 claim graph scope: {normalized}")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("exactly one active Knowledge Intelligence authorization is required")
if POST_AION210_CONTEXT:
    if active[0].get("authorization_transaction_id") not in {
        "AION-210-KI-0004",
        "AION-212-KI-0005",
        "AION-214-KI-0006",
        "AION-216-KI-0007",
    }:
        raise SystemExit(
            "AION-210-KI-0004, AION-212-KI-0005, AION-214-KI-0006, or AION-216-KI-0007 "
            "must be the sole active authorization after AION-210"
        )
    matches = [
        record
        for record in auth["records"]
        if record.get("authorization_transaction_id") == "AION-208-KI-0003"
    ]
    if len(matches) != 1:
        raise SystemExit("AION-208-KI-0003 closeout record is required")
    claim = matches[0]
    if claim.get("authorization_active") is not False:
        raise SystemExit("AION-208-KI-0003 must be inactive after AION-210")
    if claim.get("authorization_consumed") is not True:
        raise SystemExit("AION-208-KI-0003 must be consumed after AION-210")
    if claim.get("authorization_closed_by_task") != "AION-210":
        raise SystemExit("AION-208-KI-0003 must be closed by AION-210")
else:
    if active[0].get("authorization_transaction_id") != "AION-208-KI-0003":
        raise SystemExit("AION-208-KI-0003 must be the sole active authorization")
    claim = active[0]
if program["temporal_claim_evidence_graph_implemented"] is not True:
    raise SystemExit("temporal claim evidence graph implementation flag must be true")
for key in (
    "claim_graph_runtime_enabled",
    "persistent_claim_graph_write_enabled",
    "graph_database_enabled",
    "automatic_claim_extraction_enabled",
    "claim_verification_enabled",
    "truth_decision_enabled",
    "epistemic_confidence_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "runtime_effect",
):
    if program.get(key, False) is not False:
        raise SystemExit(f"program enabled prohibited graph capability: {key}")
    if claim.get(key, False) is not False:
        raise SystemExit(f"authorization enabled prohibited graph capability: {key}")
if claim["resource_limits"]["maximum_graph_write_batch"] != 0:
    raise SystemExit("maximum_graph_write_batch must remain zero")
if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
for path in run(["git", "ls-files"]).stdout.splitlines():
    suffix = Path(path).suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3", ".jsonl", ".graphml", ".gexf"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")
PY

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|subprocess|git|github)([[:space:].]|$)' \
  services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph*.py; then
  echo "ERROR: prohibited network, database, runtime, or Git import" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence claim graph authorization no-go PASS"
