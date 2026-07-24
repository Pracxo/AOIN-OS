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
    "packages/aion-sdk-python/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "services/brain-api/src/aion_brain/",
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
AION211_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/knowledge_epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_assessment.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_corroboration.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_contradiction.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_freshness.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_confidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/epistemic_evidence.py",
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
    if base:
        output = run(["git", "diff", "--name-status", base, "HEAD"]).stdout
        entries.extend(line.split("\t") for line in output.splitlines() if line.strip())
    else:
        print("WARN: comparison base unavailable; relying on current-tree checks")
    for args in (["git", "diff", "--name-status"], ["git", "diff", "--cached", "--name-status"]):
        entries.extend(line.split("\t") for line in run(args).stdout.splitlines() if line.strip())
    for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
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
        if normalized in AION211_SOURCE:
            raise SystemExit(f"AION-211 source is prohibited on AION-210: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-210 scope: {normalized}")

for relative in AION211_SOURCE:
    if (ROOT / relative).exists():
        raise SystemExit(f"AION-211 source exists before authorization implementation task: {relative}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")

harness = ROOT / "scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py"
tree = ast.parse(harness.read_text(encoding="utf-8"), filename=str(harness))
prohibited_imports = {
    "socket",
    "requests",
    "httpx",
    "aiohttp",
    "urllib" + ".request",
    "sqlite3",
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

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
for key in (
    "claim_graph_runtime_enabled",
    "persistent_claim_graph_write_enabled",
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
        raise SystemExit(f"program ledger enabled prohibited capability: {key}")
PY

if rg -n '(^|[^[:alnum:]_])(socket|requests|httpx|aiohttp|urllib\.request|sqlite3|github)([^[:alnum:]_]|$)|model provider|knowledge promotion|belief mutation|persistent write applied' \
  scripts/lib/knowledge_intelligence_claim_graph_operator_evaluation.py; then
  echo "ERROR: AION-210 harness contains prohibited runtime text" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null

echo "knowledge intelligence claim graph operator evaluation no-go PASS"
