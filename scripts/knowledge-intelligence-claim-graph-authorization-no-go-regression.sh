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
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/visual-brain.md",
    "docs/knowledge-intelligence/program-charter.md",
    "docs/knowledge-intelligence/architecture-roadmap.md",
    "docs/knowledge-intelligence/security-boundary.md",
    "docs/knowledge-intelligence/operator-model.md",
    "docs/knowledge-intelligence/program-ledger.json",
    "docs/knowledge-intelligence/authorization-ledger.json",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-architecture.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-boundary.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-data-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-relations.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-time-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-jurisdiction-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-version-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-resource-budgets.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-threat-model.md",
    "docs/knowledge-intelligence/temporal-claim-evidence-graph-roadmap.md",
    "docs/release/knowledge-intelligence-claim-graph-authorization-transaction.md",
    "docs/release/knowledge-intelligence-claim-graph-scope.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/adr/README.md",
    "operator-console-static/index.html",
    "operator-console-static/app.js",
    "operator-console-static/README.md",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
}
ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/claim-",
    "docs/knowledge-intelligence/structural-conflict-candidates.md",
    "docs/knowledge-intelligence/aion-209-checklist.md",
    "docs/release/knowledge-intelligence-claim-graph-",
    "docs/adr/0173-immutable-temporal-claim-evidence-graph-core.md",
    "examples/knowledge-intelligence/",
    "operator-console-static/demo-data/knowledge-intelligence-claim-graph",
    "services/brain-api/tests/test_knowledge_claim_graph",
)
ALLOWED_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_repository.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_index.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_integrity.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_temporal.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph_evidence.py",
}
ALLOWED_SCRIPTS = {
    "scripts/knowledge-intelligence-claim-graph-authorization-check.sh",
    "scripts/knowledge-intelligence-claim-graph-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-claim-graph-runtime-hold.sh",
    "scripts/knowledge-intelligence-claim-graph-check.sh",
    "scripts/knowledge-intelligence-claim-graph-no-go-regression.sh",
    "scripts/cognitive-local-offline-pilot-closeout-check.sh",
    "scripts/auth-design-check.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/production-auth-architecture-check.sh",
    "scripts/production-auth-core-check.sh",
    "scripts/production-auth-core-no-go-regression.sh",
    "scripts/production-auth-core-stabilization-check.sh",
    "scripts/v02-production-auth-authorization-check.sh",
    "scripts/v02-production-auth-stabilization-authorization-check.sh",
    "scripts/v02-production-auth-request-boundary-authorization-check.sh",
}
ALLOWED_TESTS = {
    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py",
    "services/brain-api/tests/test_knowledge_research_authorization_closeout.py",
    "services/brain-api/tests/test_knowledge_source_registry_evaluation_no_side_effects.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/api_support/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/config.py",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
    "services/brain-api/src/aion_brain/kernel/",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/security/",
    "services/brain-api/src/aion_brain/self_improvement/",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_",
    "services/brain-api/src/aion_brain/contracts/knowledge_research.py",
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
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


def path_allowed(path: str) -> bool:
    normalized = path.replace("\\", "/")
    if (
        normalized in ALLOWED_EXACT
        or normalized in ALLOWED_SOURCE
        or normalized in ALLOWED_SCRIPTS
        or normalized in ALLOWED_TESTS
    ):
        return True
    return any(normalized.startswith(prefix) for prefix in ALLOWED_PREFIXES)


for parts in changed_entries():
    status = parts[0]
    paths = parts[1:]
    if status.startswith(("D", "R")):
        raise SystemExit(f"destructive deletion or rename is not authorized: {parts}")
    for path in paths:
        normalized = path.replace("\\", "/")
        if Path(normalized).name in PROHIBITED_NAMES:
            raise SystemExit(f"dependency/package file changed: {normalized}")
        if any(normalized.startswith(prefix) for prefix in PROHIBITED_PREFIXES):
            if normalized not in ALLOWED_SOURCE and normalized not in ALLOWED_EXACT:
                raise SystemExit(f"prohibited runtime/workflow/dependency path changed: {normalized}")
        if not path_allowed(normalized):
            raise SystemExit(f"path outside AION-209 claim graph scope: {normalized}")

program = json.loads((ROOT / "docs/knowledge-intelligence/program-ledger.json").read_text())
auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
active = [record for record in auth["records"] if record.get("authorization_active") is True]
if len(active) != 1 or active[0].get("authorization_transaction_id") != "AION-208-KI-0003":
    raise SystemExit("AION-208-KI-0003 must be the sole active authorization")
claim = active[0]
if program["temporal_claim_evidence_graph_implemented"] is not True:
    raise SystemExit("temporal claim evidence graph implementation flag must be true")
for key in (
    "claim_graph_runtime_enabled",
    "persistent_claim_graph_write_enabled",
    "graph_database_enabled",
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
        raise SystemExit(f"program enabled prohibited graph capability: {key}")
    if claim.get(key, False) is not False:
        raise SystemExit(f"authorization enabled prohibited graph capability: {key}")
if claim["resource_limits"]["maximum_graph_write_batch"] != 0:
    raise SystemExit("maximum_graph_write_batch must remain zero")
if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
for path in run(["git", "ls-files"]).stdout.splitlines():
    suffix = Path(path).suffix.lower()
    if suffix in {".db", ".sqlite", ".sqlite3", ".jsonl", ".graphml", ".gexf"}:
        raise SystemExit(f"tracked runtime persistence file is not allowed: {path}")
PY

if rg -n '^[[:space:]]*(import|from)[[:space:]]+(socket|requests|httpx|aiohttp|urllib[.]request|sqlite3|subprocess|git|github)([[:space:].]|$)' \
  services/brain-api/src/aion_brain/contracts/knowledge_claim_graph.py \
  services/brain-api/src/aion_brain/knowledge_intelligence/claim_graph*.py; then
  echo "ERROR: prohibited network, database, runtime, or Git import" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence claim graph authorization no-go PASS"
