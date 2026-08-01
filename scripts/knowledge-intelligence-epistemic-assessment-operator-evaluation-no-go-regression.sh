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
  echo "knowledge intelligence epistemic assessment operator evaluation no-go PASS"
  exit 0
fi

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import ast
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
ALLOWED_PREFIXES = (
    "docs/",
    "examples/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
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
AION213_SOURCE_PREFIXES = (
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_",
)
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
AION217_IMPLEMENTED_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
AION219_IMPLEMENTED_STATE = (
    "controlled_public_research_pilot_implemented_operator_invoked_"
    "persistent_write_disabled_pending_closeout"
)
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
POST_AION213_SOURCE_STATES = {
    "domain_expert_mesh_implemented_persistent_write_disabled_pending_closeout",
    "tool_verification_fabric_authorized_not_implemented",
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout",
    "verified_knowledge_memory_authorized_not_implemented",
    AION217_IMPLEMENTED_STATE,
    AION219_IMPLEMENTED_STATE,
}
IMPLEMENTED_TOOL_VERIFICATION_STATE = (
    "tool_verification_fabric_implemented_persistent_write_disabled_pending_closeout"
)
PROGRAM_PATH = ROOT / "docs/knowledge-intelligence/program-ledger.json"
PROGRAM_STATE = ""
if PROGRAM_PATH.exists():
    PROGRAM_STATE = json.loads(PROGRAM_PATH.read_text()).get("program_state", "")


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
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if PROGRAM_STATE == IMPLEMENTED_TOOL_VERIFICATION_STATE and normalized in AION215_SOURCE:
            continue
        if PROGRAM_STATE == AION217_IMPLEMENTED_STATE and normalized in AION217_SOURCE:
            continue
        if PROGRAM_STATE == AION219_IMPLEMENTED_STATE and normalized in AION219_SOURCE:
            continue
        if normalized.startswith(AION213_SOURCE_PREFIXES):
            if PROGRAM_STATE not in POST_AION213_SOURCE_STATES:
                raise SystemExit(
                    f"AION-213 runtime source is not authorized in AION-212: {normalized}"
                )
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
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-212 scope: {normalized}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")

harness = ROOT / "scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py"
tree = ast.parse(harness.read_text(encoding="utf-8"), filename=str(harness))
prohibited_imports = {
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "urllib" + ".request",
    "sqlite3",
    "subprocess",
    "git",
    "github",
}
imports: set[str] = set()
for node in ast.walk(tree):
    if isinstance(node, ast.Import):
        imports.update(alias.name for alias in node.names)
    elif isinstance(node, ast.ImportFrom) and node.module:
        imports.add(node.module)
if imports & prohibited_imports:
    raise SystemExit(f"prohibited harness imports: {sorted(imports & prohibited_imports)}")
PY

if rg -n '(^|[^[:alnum:]_])(socket|requests|httpx|aiohttp|urllib\.request|sqlite3|subprocess|github)([^[:alnum:]_]|$)|model provider integration|semantic model routing|execute tools|network access enabled|human expert identity|professional credential' \
  scripts/lib/knowledge_intelligence_epistemic_assessment_operator_evaluation.py; then
  echo "ERROR: AION-212 harness contains prohibited runtime text" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null

echo "knowledge intelligence epistemic assessment operator evaluation no-go PASS"
