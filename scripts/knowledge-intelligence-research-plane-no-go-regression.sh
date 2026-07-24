#!/usr/bin/env bash
set -euo pipefail
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
export AION_REPO_ROOT="$ROOT_DIR"
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
EXPECTED_TAG = "105fe29348160a2218ac095cfffadcb6f234421f"
ALLOWED_PREFIXES = (
    "docs/knowledge-intelligence/",
    "docs/release/knowledge-intelligence-research",
    "docs/release/knowledge-intelligence-source",
    "docs/release/knowledge-intelligence-claim",
    "examples/knowledge-intelligence/",
    "operator-console-static/",
    "scripts/knowledge-intelligence-source-registry-operator-evaluation",
    "scripts/knowledge-intelligence-claim-graph",
    "services/brain-api/src/aion_brain/knowledge_intelligence/",
)
ALLOWED_EXACT = {
    "README.md",
    "AGENTS.md",
    "docs/project-status.md",
    "docs/architecture.md",
    "docs/brain-contract.md",
    "docs/policy-model.md",
    "docs/visual-brain.md",
    "docs/release/v02-release-readiness-delta.md",
    "docs/adr/README.md",
    "docs/adr/0169-controlled-research-acquisition-and-immutable-source-snapshots.md",
    "docs/adr/0170-research-acquisition-evaluation-and-source-provenance-registry-authorization.md",
    "docs/adr/0171-append-only-source-provenance-registry-core.md",
    "docs/adr/0172-source-provenance-registry-evaluation-and-temporal-claim-evidence-graph-authorization.md",
    "scripts/knowledge-intelligence-research-plane-check.sh",
    "scripts/knowledge-intelligence-research-plane-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-check.sh",
    "scripts/knowledge-intelligence-research-operator-evaluation-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-check.sh",
    "scripts/knowledge-intelligence-source-registry-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-runtime-hold.sh",
    "scripts/static-console-safety-check.sh",
    "scripts/lib/knowledge_intelligence_research_operator_evaluation.py",
    "scripts/lib/knowledge_intelligence_source_registry_operator_evaluation.py",
    "scripts/connector-no-go-regression.sh",
    "scripts/connector-runtime-no-external-call-regression.sh",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/auth-design-check.sh",
    "scripts/operator-console-static-check.sh",
    "scripts/production-auth-architecture-check.sh",
    "scripts/static-console-safety-check.sh",
    "scripts/lib/cognitive_architecture_governance.py",
    "scripts/lib/v02-production-auth-scan-exclusions.sh",
    "scripts/lib/v02_production_auth_authorization.py",
    "services/brain-api/tests/knowledge_intelligence_test_helpers.py",
    "services/brain-api/tests/knowledge_source_registry_test_helpers.py",
    "services/brain-api/tests/knowledge_source_registry_implementation_helpers.py",
    "services/brain-api/tests/knowledge_research_test_helpers.py",
    "services/brain-api/tests/test_knowledge_intelligence_cognitive_closeout_reconciliation.py",
    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_docs.py",
    "services/brain-api/tests/test_knowledge_intelligence_research_authorization_validator.py",
    "services/brain-api/tests/test_knowledge_intelligence_research_budget_spec.py",
    "services/brain-api/tests/test_self_improvement_postmerge_evidence_reconciliation.py",
    "services/brain-api/tests/test_self_improvement_shadow_activation_authorization_docs.py",
}
ALLOWED_SOURCE = {
    "services/brain-api/src/aion_brain/contracts/knowledge_research.py",
    "services/brain-api/src/aion_brain/contracts/knowledge_source_registry.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/__init__.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_policy.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_adapters.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_snapshot.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_provenance.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/source_deduplication.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_evidence.py",
    "services/brain-api/src/aion_brain/knowledge_intelligence/research_budget.py",
}
PROHIBITED_PREFIXES = (
    ".github/workflows/",
    "services/brain-api/src/aion_brain/cognitive_architecture/",
    "services/brain-api/src/aion_brain/self_improvement/",
    "services/brain-api/src/aion_brain/production_auth/",
    "services/brain-api/src/aion_brain/kernel/",
    "services/brain-api/src/aion_brain/api/",
    "services/brain-api/src/aion_brain/api_support/",
    "services/brain-api/src/aion_brain/policy/",
    "services/brain-api/src/aion_brain/audit/",
    "services/brain-api/src/aion_brain/security/",
    "services/brain-api/src/aion_brain/config.py",
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
    base_ref = os.environ.get("GITHUB_BASE_REF")
    if base_ref:
        candidates.extend([f"origin/{base_ref}", base_ref])
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
    if normalized in ALLOWED_EXACT or normalized in ALLOWED_SOURCE:
        return True
    if normalized.startswith("services/brain-api/tests/test_knowledge_research"):
        return True
    if normalized.startswith("services/brain-api/tests/test_knowledge_source"):
        return True
    if normalized.startswith("services/brain-api/tests/test_knowledge_claim"):
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
        if normalized.startswith(PROHIBITED_PREFIXES):
            raise SystemExit(f"prohibited runtime/source path changed: {normalized}")
        if not allowed(normalized):
            raise SystemExit(f"path outside AION-205 scope: {normalized}")

for source in ALLOWED_SOURCE:
    if not (ROOT / source).is_file():
        raise SystemExit(f"missing required source file: {source}")

if run(["git", "rev-parse", "aion-v0.1.0^{commit}"]).stdout.strip() != EXPECTED_TAG:
    raise SystemExit("aion-v0.1.0 tag moved")
if run(["git", "tag", "--list", "v0.2*", "aion-v0.2*"]).stdout.strip():
    raise SystemExit("v0.2 tag exists")
PY
echo "knowledge intelligence research plane no-go PASS"
