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
CLAIM_GRAPH_SOURCE = (
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
)
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/",
    "services/brain-api/pyproject.toml",
    "packages/aion-sdk-python/",
    "migrations/",
    "services/brain-api/migrations/",
    "infra/postgres/migrations/",
)
ALLOWED_PREFIXES = (
    "docs/",
    "examples/",
    "operator-console-static/",
    "scripts/",
    "services/brain-api/tests/",
)
ALLOWED_EXACT = {"README.md", "AGENTS.md"}
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
FALSE_KEYS = (
    "automatic_claim_extraction_enabled",
    "source_body_parsing_enabled",
    "raw_source_content_storage_enabled",
    "claim_verification_enabled",
    "truth_decision_enabled",
    "epistemic_confidence_enabled",
    "contradiction_resolution_enabled",
    "knowledge_promotion_enabled",
    "cognitive_belief_creation_enabled",
    "cognitive_belief_mutation_enabled",
    "persistent_claim_graph_write_enabled",
    "graph_database_enabled",
    "network_acquisition_enabled",
    "public_network_fetch_enabled",
    "search_provider_integration_enabled",
    "connector_integration_enabled",
    "model_provider_integration_enabled",
    "background_graph_worker_enabled",
    "scheduled_graph_job_enabled",
    "kernel_registration_enabled",
    "application_startup_registration_enabled",
    "api_route_enabled",
    "installed_cli_command_enabled",
    "sdk_runtime_resource_enabled",
    "credential_use_enabled",
    "cookie_use_enabled",
    "authorization_header_use_enabled",
    "source_patch_generation_enabled",
    "source_mutation_enabled",
    "worktree_creation_enabled",
    "git_mutation_enabled",
    "real_pull_request_creation_enabled",
    "approval_creation_enabled",
    "automatic_merge_enabled",
    "production_deployment_enabled",
    "model_weight_training_enabled",
    "runtime_effect",
    "dependency_change_approved",
    "migration_approved",
    "github_workflow_change_approved",
    "v02_tag_created",
    "v02_release_created",
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
    line.split("\t") for line in run(["git", "diff", "--name-status"]).stdout.splitlines() if line.strip()
)
entries.extend(
    line.split("\t") for line in run(["git", "diff", "--cached", "--name-status"]).stdout.splitlines() if line.strip()
)
for line in run(["git", "status", "--porcelain=v1"]).stdout.splitlines():
    if line.startswith("?? "):
        entries.append(["A", line[3:]])

for parts in entries:
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if normalized in CLAIM_GRAPH_SOURCE:
            raise SystemExit(f"AION-209 source is not allowed on AION-208 branch: {normalized}")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/workflow/dependency path changed: {normalized}")
        if normalized not in ALLOWED_EXACT and not any(
            normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES
        ):
            raise SystemExit(f"path outside AION-208 claim graph scope: {normalized}")

for relative in CLAIM_GRAPH_SOURCE:
    if (ROOT / relative).exists():
        raise SystemExit(f"AION-209 source exists on AION-208 branch: {relative}")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
if len(active) != 1 or active[0].get("authorization_transaction_id") != "AION-208-KI-0003":
    raise SystemExit("AION-208-KI-0003 must be the sole active authorization")
claim = active[0]
for key in FALSE_KEYS:
    if program.get(key, False) is not False:
        raise SystemExit(f"program enabled prohibited graph capability: {key}")
    if claim.get(key, False) is not False:
        raise SystemExit(f"authorization enabled prohibited graph capability: {key}")
    if claim["prohibited_capabilities"].get(key, False) is not False:
        raise SystemExit(f"prohibited capability is true: {key}")
if claim["resource_limits"]["maximum_graph_write_batch"] != 0:
    raise SystemExit("maximum_graph_write_batch must remain zero")
if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
for path in run(["git", "ls-files"]).stdout.splitlines():
    suffix = Path(path).suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3", ".jsonl"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence claim graph authorization no-go PASS"
