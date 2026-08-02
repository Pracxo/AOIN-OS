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
  echo "knowledge intelligence research operator evaluation no-go PASS"
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
EPIS_STATE = "epistemic_truth_engine_implemented_persistent_write_disabled_pending_closeout"
DOMAIN_EXPERT_STATES = {
    "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
    "tool_verification_fabric_authorized_not_implemented",
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
    "verified_knowledge_memory_authorized_not_implemented",
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout",
}
TOOL_VERIFICATION_IMPLEMENTED_STATE = (
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"
)
VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
PUBLIC_RESEARCH_PILOT_IMPLEMENTED_STATE = (
    "controlled_public_research_pilot_implemented_operator_invoked_"
    "persistent_write_disabled_pending_closeout"
)
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
}
program_state = ""
program_path = ROOT / "docs/knowledge-intelligence/program-ledger.json"
if program_path.exists():
    program_state = json.loads(program_path.read_text()).get("program_state", "")
CLAIM_GRAPH_CONTEXT = (
    program_state in {
        "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout",
        "epistemic_truth_engine_authorized_not_implemented",
        EPIS_STATE,
    }
    or os.environ.get("AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT") == "1"
    or os.environ.get("AION_AGGREGATE_GATE_RUNNING") == "1"
    or os.environ.get("AION_CHECK_RUNNING") == "1"
    or bool(os.environ.get("PYTEST_CURRENT_TEST"))
)
EPISTEMIC_ASSESSMENT_CONTEXT = (
    program_state == EPIS_STATE
    or program_state in DOMAIN_EXPERT_STATES
    or os.environ.get("AION_EPISTEMIC_ASSESSMENT_IMPLEMENTATION_CONTEXT") == "1"
    or os.environ.get("AION_AGGREGATE_GATE_RUNNING") == "1"
    or os.environ.get("AION_CHECK_RUNNING") == "1"
    or bool(os.environ.get("PYTEST_CURRENT_TEST"))
)
CLAIM_GRAPH_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
}
EPISTEMIC_ASSESSMENT_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
}
DOMAIN_EXPERT_MESH_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py",
}
AION215_SOURCE = {
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
AION217_SOURCE = {
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
AION219_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py",
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


AION222_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/governed_learning_memory.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/approval_evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/eligibility_revalidation.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_identity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/promotion_requests.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/promotion_transactions.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/rollback.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/version_planning.py",
}
AION224_GLM_STATE = (
    "governed_learning_memory_local_append_only_persistence_implemented_"
    "operator_invoked_isolated_pending_closeout"
)
AION224_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/governed_learning_memory_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/backup_restore.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_content.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/knowledge_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_persistence_policy.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_schema.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/local_sqlite_store.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/memory_projection_persistence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_approval.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/persistence_transactions.py",
}
GLM_PROGRAM_PATH = ROOT / "docs/governed-learning-memory/program-ledger.json"
GLM_PROGRAM_STATE = (
    json.loads(GLM_PROGRAM_PATH.read_text()).get("program_state", "")
    if GLM_PROGRAM_PATH.exists()
    else ""
)
AION226_GLM_STATE = (
    "governed_learning_memory_engagement_application_implemented_shadow_only_pending_closeout"
)
AION226_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/governed_engagement_learning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_identity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_adaptation_planning.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_application_approval.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_candidate_binding.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_counterfactual_evaluation.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_evidence.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_integrity.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_overlay.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_rollback.py",
    "services/brain-api/src/aion_brain/governed_learning_memory/engagement_shadow_application.py",
}

def aion241_source_allowed(path: str) -> bool:
    ledger = ROOT / "docs/v02-release-qualification/program-ledger.json"
    if not ledger.exists():
        return False
    payload = json.loads(ledger.read_text(encoding="utf-8"))
    if payload.get("controlled_staging_qualification_implemented") is not True:
        return False
    return path in set(payload.get("implemented_source_scope", ())) and (
        path == "services/brain-api/src/aion_brain/contracts/v02_staging_qualification.py"
        or path.startswith("services/brain-api/src/aion_brain/v02_staging_qualification/")
    )

def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        candidates.extend([f"origin/{base_ref}", base_ref])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge_base.returncode == 0 and merge_base.stdout.strip():
                return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


entries: list[list[str]] = []
base = comparison_base()
if base:
    entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip())
else:
    print("WARN: comparison base unavailable; relying on current-tree checks")
entries.extend(line.split("\t") for line in run(["git", "diff", "--name-status"]).stdout.splitlines() if line.strip())
entries.extend(line.split("\t") for line in run(["git", "diff", "--cached", "--name-status"]).stdout.splitlines() if line.strip())
for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
    if line.startswith("?? "):
        entries.append(["A", line[3:]])

for parts in entries:
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if CLAIM_GRAPH_CONTEXT and normalized in CLAIM_GRAPH_SOURCE:
            continue
        if EPISTEMIC_ASSESSMENT_CONTEXT and normalized in EPISTEMIC_ASSESSMENT_SOURCE:
            continue
        if program_state in DOMAIN_EXPERT_STATES and normalized in DOMAIN_EXPERT_MESH_SOURCE:
            continue
        if program_state in {TOOL_VERIFICATION_IMPLEMENTED_STATE, VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE} and normalized in AION215_SOURCE:
            continue
        if program_state == VERIFIED_KNOWLEDGE_IMPLEMENTED_STATE and normalized in AION217_SOURCE:
            continue
        if program_state == PUBLIC_RESEARCH_PILOT_IMPLEMENTED_STATE and normalized in AION219_SOURCE:
            continue
        if normalized in AION222_SOURCE:
            continue
        if GLM_PROGRAM_STATE == AION224_GLM_STATE and normalized in AION224_SOURCE:
            continue
        if GLM_PROGRAM_STATE == AION226_GLM_STATE and normalized in AION226_SOURCE:
            continue
        if (
            GLM_PROGRAM_STATE == "governed_learning_memory_controlled_local_continual_learning_pilot_implemented_completed_pending_final_closeout"
            and (
                normalized == "services/brain-api/src/aion_brain/contracts/governed_continual_learning.py"
                or normalized == "services/brain-api/src/aion_brain/governed_learning_memory/__init__.py"
                or normalized.startswith("services/brain-api/src/aion_brain/governed_learning_memory/continual_learning_")
            )
        ):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/secure_runtime.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/secure_runtime/"
        ):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/model_gateway.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/model_gateway/"
        ):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/sandboxed_capability_runtime.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/capability_runtime/"
        ):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/operator_console_integration.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/operator_console_runtime/"
        ):
            continue
        if normalized == "services/brain-api/src/aion_brain/contracts/v02_release_qualification.py" or normalized.startswith(
            "services/brain-api/src/aion_brain/v02_release_qualification/"
        ):
            continue
        if aion241_source_allowed(normalized):
            continue
        if normalized.startswith(PROHIBITED_PREFIXES) and normalized not in ALLOWED_EXACT:
            raise SystemExit(f"runtime/source/workflow path changed on AION-206: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES):
            raise SystemExit(f"path outside AION-206 scope: {normalized}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
PY

HARNESS="scripts/lib/knowledge_intelligence_research_operator_evaluation.py"
test -f "$HARNESS"

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|subprocess|git|github)([[:space:].]|$)' "$HARNESS"; then
  echo "ERROR: prohibited network/Git import detected in AION-206 harness" >&2
  exit 1
fi

if rg -n '(knowledge_candidate_created[[:space:]]*=[[:space:]]*True|belief_created[[:space:]]*=[[:space:]]*True|approval_created[[:space:]]*=[[:space:]]*True|authorization_created[[:space:]]*=[[:space:]]*True|runtime_effect[[:space:]]*=[[:space:]]*True)' "$HARNESS"; then
  echo "ERROR: AION-206 harness attempts to create forbidden effects" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "knowledge intelligence research operator evaluation no-go PASS"
