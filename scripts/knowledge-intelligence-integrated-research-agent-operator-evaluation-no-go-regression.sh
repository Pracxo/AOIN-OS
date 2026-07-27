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
AION217_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/knowledge_verified_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_memory.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_lineage.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_versioning.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_revalidation.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_signal_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/engagement_learning_candidates.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/verified_knowledge_evidence.py",
}
AION217_IMPLEMENTED_PROGRAM_STATE = (
    "verified_knowledge_memory_implemented_persistent_write_disabled_pending_closeout"
)
AION219_IMPLEMENTED_PROGRAM_STATE = (
    "controlled_public_research_pilot_implemented_operator_invoked_"
    "persistent_write_disabled_pending_closeout"
)
AION219_SOURCE_PATHS = {
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
PERSISTENCE_SUFFIXES = (".db", ".sqlite", ".sqlite3", ".jsonl", ".tool-state", ".state")
FORBIDDEN_PY_IMPORTS = (
    "import socket",
    "import requests",
    "import httpx",
    "import aiohttp",
    "import urllib" ".request",
    "import sqlite3",
    "import subprocess",
    "import git",
    "import github",
    "from socket",
    "from requests",
    "from httpx",
    "from aiohttp",
    "from urllib" ".request",
    "from sqlite3",
    "from subprocess",
    "from git",
    "from github",
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


def python_runtime_import_scan_text(relative: str) -> str:
    base = comparison_base()
    if base is not None:
        exists_at_base = run(["git", "cat-file", "-e", f"{base}:{relative}"], check=False)
        if exists_at_base.returncode == 0:
            diff = run(["git", "diff", "--unified=0", base, "--", relative], check=False)
            added_lines = [
                line[1:]
                for line in diff.stdout.splitlines()
                if line.startswith("+") and not line.startswith("+++")
            ]
            return "\n".join(added_lines).lower()
    return (ROOT / relative).read_text(encoding="utf-8").lower()


changed_paths: set[str] = set()
program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
aion217_implemented = program.get("program_state") in {
    AION217_IMPLEMENTED_PROGRAM_STATE,
    AION219_IMPLEMENTED_PROGRAM_STATE,
}
for parts in changed_entries():
    status, paths = parts[0], parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        changed_paths.add(normalized)
        name = Path(normalized).name
        if name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized in AION217_SOURCE_PATHS:
            if aion217_implemented:
                continue
            raise SystemExit(f"AION-217 source is not authorized on AION-216: {normalized}")
        if normalized in AION219_SOURCE_PATHS:
            continue
        if any(normalized.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/workflow/package/migration path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-216 integrated evaluation scope: {normalized}")

for relative in run(["git", "ls-files"]).stdout.splitlines():
    if relative.endswith(PERSISTENCE_SUFFIXES):
        raise SystemExit(f"tracked persistence file detected: {relative}")

for relative in sorted(changed_paths):
    if relative in AION219_SOURCE_PATHS:
        continue
    if relative.startswith("services/brain-api/tests/") or not relative.endswith(".py"):
        continue
    lowered = python_runtime_import_scan_text(relative)
    for marker in FORBIDDEN_PY_IMPORTS:
        if marker in lowered:
            raise SystemExit(f"forbidden runtime import in changed Python file {relative}: {marker}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence integrated research agent operator evaluation no-go PASS"
