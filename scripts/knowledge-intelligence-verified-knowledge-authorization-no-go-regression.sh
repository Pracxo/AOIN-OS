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
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import os, subprocess
from pathlib import Path
ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
ALLOWED_PREFIXES = ("docs/", "examples/", "operator-console-static/", "scripts/", "services/brain-api/tests/")
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
PROHIBITED_PREFIXES = (".github/workflows/", "services/brain-api/src/aion_brain/", "services/brain-api/pyproject.toml", "packages/aion-sdk-python/src/", "migrations/", "services/brain-api/migrations/", "infra/postgres/migrations/")
PROHIBITED_NAMES = {"package.json", "package-lock.json", "pnpm-lock.yaml", "yarn.lock", "bun.lockb", "poetry.lock", "uv.lock", "Pipfile", "Pipfile.lock"}
PERSISTENCE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".jsonl", ".state")
AION217_SOURCE_PATHS = {"services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py", "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py", "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py", "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py", "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py"}
AION219_SOURCE_PATHS = {"services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py", "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py", "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py"}
FORBIDDEN_CHANGED_CODE = ("automatic_candidate_approval_enabled = True", "automatic_verified_knowledge_promotion_enabled = True", "engagement_signal_as_fact_enabled = True", "engagement_confidence_effect_enabled = True", "tool_output_as_verified_fact_enabled = True", "model_output_as_verified_fact_enabled = True", "domain_mesh_consensus_as_truth_enabled = True", "public_network_fetch_enabled = True", "actual_tool_execution_enabled = True", "persistent_verified_knowledge_write_enabled = True", "cognitive_memory_write_enabled = True", "belief_mutation_enabled = True")
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
    __import__("json").loads(GLM_PROGRAM_PATH.read_text()).get("program_state", "")
    if GLM_PROGRAM_PATH.exists()
    else ""
)

def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]: return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)
def ref_exists(ref: str) -> bool: return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0
def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base: candidates.extend([f"origin/{github_base}", github_base])
    candidates.extend(["origin/main", "main"])
    for candidate in candidates:
        if ref_exists(candidate):
            merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
            if merge_base.returncode == 0 and merge_base.stdout.strip(): return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None
def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []; base = comparison_base()
    if base is not None: entries.extend(line.split("	") for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines() if line.strip())
    else: print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]): entries.extend(line.split("	") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1", "--untracked-files=all"]).stdout.splitlines():
        if line.startswith("?? "): entries.append(["A", line[3:]])
    return entries
changed_paths: set[str] = set()
for parts in changed_entries():
    status, paths = parts[0], parts[1:]
    if status.startswith(("D", "R")): raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/"); changed_paths.add(normalized); name = Path(normalized).name
        if name in PROHIBITED_NAMES: raise SystemExit(f"package or dependency file changed: {normalized}")
        if normalized in AION217_SOURCE_PATHS or normalized in AION219_SOURCE_PATHS: continue
        if normalized in AION222_SOURCE: continue
        if GLM_PROGRAM_STATE == AION224_GLM_STATE and normalized in AION224_SOURCE: continue
        if any(normalized.startswith(prefix) for prefix in PROHIBITED_PREFIXES): raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES): raise SystemExit(f"path outside AION-217 scope: {normalized}")
for relative in run(["git", "ls-files"]).stdout.splitlines():
    if relative.endswith(PERSISTENCE_SUFFIXES): raise SystemExit(f"tracked state file detected: {relative}")
for relative in sorted(changed_paths):
    if relative in {"scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh", "scripts/knowledge-intelligence-verified-knowledge-no-go-regression.sh"}:
        continue
    if not relative.endswith((".py", ".sh", ".js")) or relative.startswith("services/brain-api/tests/"): continue
    text = (ROOT / relative).read_text(encoding="utf-8")
    for marker in FORBIDDEN_CHANGED_CODE:
        if marker in text: raise SystemExit(f"forbidden enabled runtime marker in {relative}: {marker}")
if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG: raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip(): raise SystemExit("v0.2 tag exists")
PY
aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi
echo "knowledge intelligence verified knowledge authorization no-go PASS"
