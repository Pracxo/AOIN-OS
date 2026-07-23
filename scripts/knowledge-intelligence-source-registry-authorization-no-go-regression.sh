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
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/src/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
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
AION207_RUNTIME_PATHS = (
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
)


def run(args: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(args, cwd=ROOT, text=True, capture_output=True, check=check)


def ref_exists(ref: str) -> bool:
    return run(["git", "rev-parse", "--verify", "--quiet", ref], check=False).returncode == 0


def comparison_base() -> str | None:
    candidates: list[str] = []
    github_base_ref = os.environ.get("GITHUB_BASE_REF")
    if github_base_ref:
        candidates.extend([f"origin/{github_base_ref}", github_base_ref])
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


def allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    return normalized in ALLOWED_EXACT or any(
        normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
    )


for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"runtime/source/workflow path changed on AION-206: {normalized}")
        if not allowed(normalized):
            raise SystemExit(f"path outside AION-206 source registry scope: {normalized}")

for relative in AION207_RUNTIME_PATHS:
    if (ROOT / relative).exists():
        raise SystemExit(f"AION-207 runtime source added by AION-206: {relative}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")

for path in sorted((ROOT / "examples/knowledge-intelligence").glob("source-registry*.json")):
    payload = json.loads(path.read_text())
    if payload.get("research_runtime_enabled") is not False:
        raise SystemExit(f"research runtime enabled in {path}")
    if payload.get("network_access_enabled") is not False:
        raise SystemExit(f"network access enabled in {path}")
    if payload.get("source_body_persistence_enabled") is not False:
        raise SystemExit(f"source body persistence enabled in {path}")
    prohibited = payload.get("prohibited_capabilities", {})
    for key, value in prohibited.items():
        if value is not False:
            raise SystemExit(f"prohibited capability enabled in {path}: {key}")
    rendered = json.dumps(payload, sort_keys=True).lower()
    for marker in (
        '"implementation_approved": true',
        '"privileged_bypass_enabled": true',
        '"access_control_bypass_enabled": true',
        '"claim_verification_enabled": true',
        '"knowledge_promotion_enabled": true',
        '"belief_mutation_enabled": true',
        '"source_body_persistence_enabled": true',
        '"network_access_enabled": true',
    ):
        if marker in rendered:
            raise SystemExit(f"forbidden enabled marker in {path}: {marker}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "knowledge intelligence source registry authorization no-go PASS"
