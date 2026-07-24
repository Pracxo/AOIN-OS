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

AION207_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_evidence.py",
}
CLAIM_GRAPH_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
}
PROHIBITED_SOURCE = {
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_runtime.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_registry_service.py",
    "services/brain-api/src/aion_brain/api/source_registry.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
    "packages/aion-sdk-python/src/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/api_support/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/kernel/",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/security/",
    "services/brain-api/src/aion_brain/self_improvement/",
)
PROHIBITED_AION205_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_research.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_adapters.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_snapshot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_provenance.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_deduplication.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_budget.py",
}
ALLOWED_PREFIXES = (
    "docs/",
    "examples/knowledge-intelligence/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {"README.md", "AGENTS.md"} | AION207_SOURCE
program_state = ""
program_path = ROOT / "docs/knowledge-intelligence/program-ledger.json"
if program_path.exists():
    program_state = json.loads(program_path.read_text()).get("program_state", "")
CLAIM_GRAPH_CONTEXT = (
    program_state == "temporal_claim_evidence_graph_implemented_write_disabled_pending_closeout"
    or os.environ.get("AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT") == "1"
    or os.environ.get("AION_AGGREGATE_GATE_RUNNING") == "1"
    or os.environ.get("AION_CHECK_RUNNING") == "1"
    or bool(os.environ.get("PYTEST_CURRENT_TEST"))
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
    return (
        normalized in ALLOWED_EXACT
        or (CLAIM_GRAPH_CONTEXT and normalized in CLAIM_GRAPH_SOURCE)
        or any(
        normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
    )
    )


for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        name = Path(normalized).name
        if name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized in PROHIBITED_AION205_SOURCE:
            raise SystemExit(f"AION-205 acquisition source changed: {normalized}")
        if normalized in PROHIBITED_SOURCE:
            raise SystemExit(f"source registry runtime/API path added: {normalized}")
        if CLAIM_GRAPH_CONTEXT and normalized in CLAIM_GRAPH_SOURCE:
            continue
        if normalized.startswith("services/brain-api/src/aion_brain/") and normalized not in AION207_SOURCE:
            raise SystemExit(f"path outside exact AION-207 source scope: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime, workflow, migration, SDK, API, policy, audit, security, kernel, or config path changed: {normalized}")
        if not allowed(normalized):
            raise SystemExit(f"path outside AION-207 source registry scope: {normalized}")

for relative in PROHIBITED_SOURCE:
    if (ROOT / relative).exists():
        raise SystemExit(f"prohibited source registry runtime surface exists: {relative}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")

tracked = run(["git", "ls-files"]).stdout.splitlines()
for path in tracked:
    suffix = Path(path).suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3", ".jsonl"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")

for path in sorted((ROOT / "examples/knowledge-intelligence").glob("source-registry*.json")) + sorted(
    (ROOT / "operator-console-static/demo-data").glob("knowledge-intelligence-source-registry*.json")
):
    payload = json.loads(path.read_text())
    rendered = json.dumps(payload, sort_keys=True).lower()
    for marker in (
        '"source_body_present": true',
        '"source_body_persistence_enabled": true',
        '"claim_verification_enabled": true',
        '"knowledge_promotion_enabled": true',
        '"belief_mutation_enabled": true',
        '"source_registry_runtime_enabled": true',
        '"source_registry_persistent_write_enabled": true',
        '"network_access_enabled": true',
        '"runtime_effect": true',
        '"persistent_write_applied": true',
        '"implementation_approved": true',
        '"privileged_bypass_enabled": true',
        '"access_control_bypass_enabled": true',
    ):
        if marker in rendered:
            raise SystemExit(f"forbidden enabled marker in {path}: {marker}")
    if "http://" in rendered or "https://" in rendered:
        raise SystemExit(f"live URL is not allowed in source registry evidence: {path}")
    if "source_body_bytes" in rendered:
        def walk(value: object) -> None:
            if isinstance(value, dict):
                for key, nested in value.items():
                    if key == "source_body_bytes" and nested != 0:
                        raise SystemExit(f"source body bytes must remain zero: {path}")
                    walk(nested)
            elif isinstance(value, list):
                for item in value:
                    walk(item)
        walk(payload)
PY

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|subprocess|git|github)([[:space:].]|$)' \
  services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/source_registry*.py; then
  echo "ERROR: prohibited runtime, network, database, or Git import" >&2
  exit 1
fi

if rg -n 'def[[:space:]]+(update|delete|truncate|compact|overwrite|save|commit|connect|migrate)|write_text|open[[:space:]]*\(|create_pull|automatic_merge|deployment_enabled[[:space:]]*=[[:space:]]*True|model_weight_training' \
  services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/source_registry*.py; then
  echo "ERROR: prohibited mutation, persistence, PR, merge, deployment, or training surface" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence source registry authorization no-go PASS"
