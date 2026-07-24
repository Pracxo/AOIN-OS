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
)
PROHIBITED_SOURCE_PREFIXES = (
    "services/brain-api/src/aion_brain/",
    "services/brain-api/src/aion_brain/api/",
)
CLAIM_GRAPH_CONTEXT = any(
    os.environ.get(key) == "1"
    for key in (
        "AION_CLAIM_GRAPH_IMPLEMENTATION_CONTEXT",
        "AION_AGGREGATE_GATE_RUNNING",
        "AION_CHECK_RUNNING",
    )
)
CLAIM_GRAPH_SOURCE_PATHS = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
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
DISABLED_KEYS = (
    "research_runtime_enabled",
    "source_registry_runtime_enabled",
    "source_registry_persistent_write_enabled",
    "source_body_persistence_enabled",
    "claim_verification_enabled",
    "knowledge_promotion_enabled",
    "belief_mutation_enabled",
    "network_access_enabled",
    "public_network_fetch_available",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "source_mutation_enabled",
    "git_mutation_enabled",
    "runtime_created_pr_enabled",
    "runtime_pr_enabled",
    "automatic_merge_enabled",
    "deployment_enabled",
    "model_provider_integration_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
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
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited package/workflow/migration path changed: {normalized}")
        if normalized.startswith(PROHIBITED_SOURCE_PREFIXES):
            if CLAIM_GRAPH_CONTEXT and normalized in CLAIM_GRAPH_SOURCE_PATHS:
                continue
            raise SystemExit(f"runtime source path changed on AION-208: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-208 scope: {normalized}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
records = auth["records"]
active = [record for record in records if record.get("authorization_active") is True]
if len(active) != 1:
    raise SystemExit("exactly one active Knowledge Intelligence authorization is required")

source_records = [
    record for record in records if record.get("authorization_transaction_id") == "AION-206-KI-0002"
]
if len(source_records) != 1:
    raise SystemExit("AION-206-KI-0002 source registry authorization record is required")
source_record = source_records[0]
active_record = active[0]
for key in DISABLED_KEYS:
    if program.get(key) is not False:
        raise SystemExit(f"program ledger enabled prohibited capability: {key}")
    if source_record.get(key, False) is not False:
        raise SystemExit(f"AION-206 authorization enabled prohibited capability: {key}")

if program["source_provenance_registry_implemented"] is not True:
    raise SystemExit("source registry implementation flag must remain true")
if program["source_provenance_registry_state"] != (
    "implemented_append_only_in_memory_replay_persistent_write_disabled"
):
    raise SystemExit("source registry must remain in-memory with persistent writes disabled")
if source_record["resource_limits"]["maximum_registry_write_batch"] != 0:
    raise SystemExit("source registry write batch budget must remain zero")

active_id = active_record.get("authorization_transaction_id")
if active_id == "AION-206-KI-0002":
    if source_record["authorization_consumed"] is not False:
        raise SystemExit("pre-closeout AION-206 authorization must not be consumed")
    if source_record["authorization_expired"] is not False:
        raise SystemExit("pre-closeout AION-206 authorization must not be expired")
elif active_id == "AION-208-KI-0003":
    if source_record["authorization_consumed"] is not True:
        raise SystemExit("AION-206 authorization must be consumed after AION-208")
    if source_record["authorization_expired"] is not True:
        raise SystemExit("AION-206 authorization must be expired after AION-208")
    if source_record.get("authorization_closed_by_task") != "AION-208":
        raise SystemExit("AION-206 authorization must be closed by AION-208")
    if active_record["implementation_task"] != "AION-209":
        raise SystemExit("AION-208 authorization must point only to AION-209")
    for key in DISABLED_KEYS:
        if active_record.get(key, False) is not False:
            raise SystemExit(f"AION-208 authorization enabled prohibited capability: {key}")
elif active_id == "AION-210-KI-0004":
    if source_record["authorization_consumed"] is not True:
        raise SystemExit("AION-206 authorization must be consumed after AION-208")
    if source_record["authorization_expired"] is not True:
        raise SystemExit("AION-206 authorization must be expired after AION-208")
    if source_record.get("authorization_closed_by_task") != "AION-208":
        raise SystemExit("AION-206 authorization must be closed by AION-208")
    claim_records = [
        record
        for record in records
        if record.get("authorization_transaction_id") == "AION-208-KI-0003"
    ]
    if len(claim_records) != 1:
        raise SystemExit("AION-208 authorization closeout record is required")
    claim_record = claim_records[0]
    if claim_record.get("authorization_active") is not False:
        raise SystemExit("AION-208 authorization must be inactive after AION-210")
    if claim_record.get("authorization_consumed") is not True:
        raise SystemExit("AION-208 authorization must be consumed after AION-210")
    if claim_record.get("authorization_expired") is not True:
        raise SystemExit("AION-208 authorization must be expired after AION-210")
    if claim_record.get("authorization_closed_by_task") != "AION-210":
        raise SystemExit("AION-208 authorization must be closed by AION-210")
    if active_record["implementation_task"] != "AION-211":
        raise SystemExit("AION-210 authorization must point only to AION-211")
    for key in DISABLED_KEYS:
        if active_record.get(key, False) is not False:
            raise SystemExit(f"AION-210 authorization enabled prohibited capability: {key}")
else:
    raise SystemExit(f"unexpected active Knowledge Intelligence authorization: {active_id}")

tree = ast.parse(
    (ROOT / "scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py").read_text(),
    filename="knowledge_intelligence_source_registry_operator_evaluation.py",
)
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
PY

if rg -n '(claim_verified[[:space:]]*=[[:space:]]*True|knowledge_promoted[[:space:]]*=[[:space:]]*True|belief_created[[:space:]]*=[[:space:]]*True|belief_mutated[[:space:]]*=[[:space:]]*True|persistent_write_applied[[:space:]]*=[[:space:]]*True|runtime_effect[[:space:]]*=[[:space:]]*True)' \
  scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py; then
  echo "ERROR: AION-208 harness attempts to create forbidden runtime effects" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null

echo "knowledge intelligence source registry operator evaluation no-go PASS"
