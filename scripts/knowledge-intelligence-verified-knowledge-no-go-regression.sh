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

import os
import re
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_V01_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"

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
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/",
    "packages/aion-sdk-python/src/",
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
PERSISTENCE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".jsonl", ".state")
AION217_SOURCE_PATHS = {
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
FORBIDDEN_RUNTIME_MARKERS = (
    "verified_knowledge_runtime_enabled = True",
    "persistent_verified_knowledge_write_enabled = True",
    "verified_knowledge_database_enabled = True",
    "automatic_verified_knowledge_promotion_enabled = True",
    "automatic_candidate_approval_enabled = True",
    "cognitive_memory_write_enabled = True",
    "belief_mutation_enabled = True",
    "engagement_signal_as_fact_enabled = True",
    "engagement_confidence_effect_enabled = True",
    "public_network_fetch_enabled = True",
    "actual_tool_execution_enabled = True",
    "user_acceptance_as_truth_enabled = True",
    "user_rejection_as_refutation_enabled = True",
    "repetition_as_corroboration_enabled = True",
    "citation_click_as_corroboration_enabled = True",
    "popularity_as_truth_enabled = True",
    "tool_output_as_verified_fact_enabled = True",
    "model_output_as_verified_fact_enabled = True",
    "domain_mesh_consensus_as_truth_enabled = True",
)
PROHIBITED_IMPORT_RE = re.compile(
    r"^\s*(?:import|from)\s+"
    r"(subprocess|socket|requests|httpx|aiohttp|urllib\.request|sqlite3|git|"
    r"github|selenium|playwright)(?:[\s.]|$)",
    re.MULTILINE,
)
PROHIBITED_CALL_RE = re.compile(
    r"os\.system|subprocess\.|Popen\(|check_output\(|check_call\(|eval\(|exec\(|"
    r"\.write_text\(|\.write_bytes\(|\.unlink\(|\.rename\(|\.replace\(|\.touch\("
)
PROHIBITED_REGISTRATION_RE = re.compile(
    r"api_router|APIRouter|"
    r"click\.command|typer\.Typer|argparse\.ArgumentParser|git (?:push|commit|tag)|"
    r"gh pr create|runtime_pull_request\(|runtime_approval\(",
    re.IGNORECASE,
)
PROHIBITED_TRUE_BOUNDARY_RE = re.compile(
    r"(?:scheduler_invoked|background_worker_invoked|kernel_registration_enabled|"
    r"application_startup_registration_enabled|runtime_created_pr_enabled|"
    r"approval_creation_enabled)\s*(?::\s*Literal\[True\]|=\s*True)"
)


def run(args: list[str], *, check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates = ["origin/main", "main"]
    github_base = os.environ.get("GITHUB_BASE_REF")
    if github_base:
        candidates.extend([f"origin/{github_base}", github_base])
    for candidate in candidates:
        if not ref_exists(candidate):
            continue
        merge_base = run(["git", "merge-base", "HEAD", candidate], check=False)
        if merge_base.returncode == 0 and merge_base.stdout.strip():
            return merge_base.stdout.strip()
    return "HEAD~1" if ref_exists("HEAD~1") else None


def changed_entries() -> list[list[str]]:
    entries: list[list[str]] = []
    base = comparison_base()
    if base is None:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    else:
        output = run(["git", "diff", "--name-status", base, "HEAD"]).stdout
        entries.extend(line.split("\t") for line in output.splitlines() if line.strip())
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        output = run(args).stdout
        entries.extend(line.split("\t") for line in output.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
        if line.startswith("?? "):
            entries.append(["A", line[3:]])
    return entries


changed_paths: set[str] = set()
for parts in changed_entries():
    status, paths = parts[0], parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        changed_paths.add(normalized)
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"package or dependency file changed: {normalized}")
        if normalized in AION217_SOURCE_PATHS:
            continue
        if any(normalized.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            raise SystemExit(f"protected runtime/workflow/package path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-217 scope: {normalized}")

for relative in run(["git", "ls-files"]).stdout.splitlines():
    if relative.endswith(PERSISTENCE_SUFFIXES):
        raise SystemExit(f"tracked persistence/state file detected: {relative}")

for relative in sorted(AION217_SOURCE_PATHS):
    path = ROOT / relative
    if not path.exists():
        continue
    text = path.read_text(encoding="utf-8")
    if PROHIBITED_IMPORT_RE.search(text):
        raise SystemExit(f"prohibited runtime/network/database/process import in {relative}")
    if PROHIBITED_CALL_RE.search(text):
        raise SystemExit(f"prohibited execution or filesystem mutation call in {relative}")
    if PROHIBITED_REGISTRATION_RE.search(text):
        raise SystemExit(f"prohibited API/CLI/startup/scheduler/runtime marker in {relative}")
    if PROHIBITED_TRUE_BOUNDARY_RE.search(text):
        raise SystemExit(f"prohibited true runtime boundary marker in {relative}")
    for marker in FORBIDDEN_RUNTIME_MARKERS:
        if marker in text:
            raise SystemExit(f"forbidden runtime marker in {relative}: {marker}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_V01_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
unexpected_v02_tags = [
    tag
    for tag in run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.splitlines()
    if tag != "aion-v0.2.0-rc.1"
]
if unexpected_v02_tags:
    raise SystemExit(f"unexpected v0.2 tag exists: {unexpected_v02_tags}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence verified knowledge memory no-go PASS"
