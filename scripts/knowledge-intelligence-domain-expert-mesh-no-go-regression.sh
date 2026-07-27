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

import json
import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])

ALLOWED_PREFIXES = (
    "docs/",
    "examples/knowledge-intelligence/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/pyproject.toml",
    "packages/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
PROHIBITED_EXACT = {
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_model_provider.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_tools.py",
    "services/brain-api/src/aion_brain/api/domain_expert_mesh.py",
}
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
PERSISTENCE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".jsonl", ".mesh-state", ".state")
AION217_ALLOWED_SOURCE_PATHS = {
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
AION217_IMPLEMENTED_PROGRAM_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
AION219_IMPLEMENTED_PROGRAM_STATE = (
    "controlled_public_research_pilot_implemented_operator_invoked_"
    "persistent_write_disabled_pending_closeout"
)
AION219_ALLOWED_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/knowledge_public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_dns.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_http_transport.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_claims.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_pilot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_session.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/public_research_integrity.py",
}
PROGRAM_PATH = ROOT / "docs/knowledge-intelligence/program-ledger.json"
PROGRAM_STATE = (
    json.loads(PROGRAM_PATH.read_text()).get("program_state", "")
    if PROGRAM_PATH.exists()
    else ""
)


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
    if base is not None:
        entries.extend(
            line.split("\t")
            for line in run(["git", "diff", "--name-status", base, "HEAD"]).stdout.splitlines()
            if line.strip()
        )
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


for parts in changed_entries():
    status, paths = parts[0], parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized in PROHIBITED_EXACT:
            raise SystemExit(f"unauthorized runtime path changed: {normalized}")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if PROGRAM_STATE in {
            AION217_IMPLEMENTED_PROGRAM_STATE,
            AION219_IMPLEMENTED_PROGRAM_STATE,
        } and normalized in AION217_ALLOWED_SOURCE_PATHS:
            continue
        if normalized in AION219_ALLOWED_SOURCE_PATHS:
            continue
        if normalized not in ALLOWED_EXACT and normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-213 scope: {normalized}")

for relative in run(["git", "ls-files"]).stdout.splitlines():
    if relative.endswith(PERSISTENCE_SUFFIXES):
        raise SystemExit(f"tracked persistence file detected: {relative}")
PY

domain_expert_source_paths=(
  services/brain-api/src/aion_brain/contracts/knowledge_domain_expert_mesh.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_mesh.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_profiles.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_routing.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_deliberation.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_synthesis.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_integrity.py
  services/brain-api/src/aion_brain/knowledge_intelligence/domain_expert_evidence.py
)

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|sqlalchemy|aiosqlite)([[:space:].]|$)|APIRouter|FastAPI|@router|@app|BackgroundTasks|create_engine' \
  "${domain_expert_source_paths[@]}"; then
  echo "ERROR: unauthorized mesh runtime, network, API, worker, or database surface detected" >&2
  exit 1
fi

if rg -n '^[[:space:]]*import[[:space:]]+random|^[[:space:]]*from[[:space:]]+random[[:space:]]+import|Literal\[True\].*(model_provider|tool_execution|network_access|persistent_write|knowledge_promoted|belief_mutated|claim_accepted|claim_rejected)|=.*True.*(model_provider|tool_execution|network_access|persistent_write_applied|knowledge_promoted|belief_mutated|claim_accepted|claim_rejected)|learned_expert_routing_enabled:[[:space:]]*Literal\[True\]|hidden_routing_weight_enabled:[[:space:]]*Literal\[True\]|embedding_classification_enabled:[[:space:]]*Literal\[True\]' \
  "${domain_expert_source_paths[@]}"; then
  echo "ERROR: prohibited mesh behavior detected in source" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence domain expert mesh no-go PASS"
