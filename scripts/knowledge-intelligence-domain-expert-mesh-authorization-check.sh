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

./scripts/knowledge-intelligence-domain-expert-mesh-authorization-no-go-regression.sh

"$PYTHON_BIN" -m json.tool examples/knowledge-intelligence/domain-expert-mesh-authorization.json >/dev/null
"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import json
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
module_path = ROOT / "scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py"
spec = importlib.util.spec_from_file_location("mesh_auth", module_path)
assert spec is not None and spec.loader is not None
mesh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mesh)

required_files = (
    "docs/knowledge-intelligence/domain-expert-mesh-architecture.md",
    "docs/knowledge-intelligence/domain-expert-mesh-boundary.md",
    "docs/knowledge-intelligence/domain-taxonomy-model.md",
    "docs/knowledge-intelligence/domain-expert-profile-model.md",
    "docs/knowledge-intelligence/domain-expert-case-model.md",
    "docs/knowledge-intelligence/domain-expert-routing-model.md",
    "docs/knowledge-intelligence/domain-expert-panel-policy.md",
    "docs/knowledge-intelligence/domain-expert-independence.md",
    "docs/knowledge-intelligence/domain-expert-report-model.md",
    "docs/knowledge-intelligence/domain-expert-critique-model.md",
    "docs/knowledge-intelligence/domain-expert-disagreement-model.md",
    "docs/knowledge-intelligence/domain-expert-synthesis-policy.md",
    "docs/knowledge-intelligence/domain-expert-high-stakes-policy.md",
    "docs/knowledge-intelligence/domain-expert-resource-budgets.md",
    "docs/knowledge-intelligence/domain-expert-threat-model.md",
    "docs/knowledge-intelligence/domain-expert-mesh-roadmap.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-authorization-transaction.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-scope.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-runtime-hold.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-no-go.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-checklist.md",
    "docs/release/knowledge-intelligence-domain-expert-mesh-evidence-matrix.md",
    "examples/knowledge-intelligence/domain-expert-mesh-authorization.json",
    "examples/knowledge-intelligence/domain-taxonomy-node.json",
    "examples/knowledge-intelligence/domain-expert-profile.json",
    "examples/knowledge-intelligence/domain-expert-case.json",
    "examples/knowledge-intelligence/expert-panel-plan.json",
    "examples/knowledge-intelligence/expert-perspective-report.json",
    "examples/knowledge-intelligence/expert-critique.json",
    "examples/knowledge-intelligence/expert-disagreement-item.json",
    "examples/knowledge-intelligence/expert-mesh-synthesis.json",
    "examples/knowledge-intelligence/domain-expert-mesh-resource-budget.json",
    "examples/knowledge-intelligence/domain-expert-mesh-runtime-hold.json",
    "examples/knowledge-intelligence/domain-expert-mesh-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-panel.json",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-disagreement.json",
    "operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-runtime-hold.json",
)
for relative in required_files:
    if not (ROOT / relative).is_file():
        raise SystemExit(f"required domain expert mesh evidence file missing: {relative}")

mesh.validate_authorization_files(ROOT)

report = json.loads(
    (ROOT / "examples/knowledge-intelligence/epistemic-assessment-operator-evaluation-report.json").read_text()
)
if report["decision"] != mesh.PARENT_DECISION or report["evaluation_passed"] is not True:
    raise SystemExit("AION-EAE-001 must pass before AION-212-KI-0005 is active")
closeout = report["authorization_closeout"]
if closeout["authorization_transaction_id"] != mesh.PARENT_AUTHORIZATION_ID:
    raise SystemExit("AION-210-KI-0004 closeout evidence missing")
if closeout["authorization_active"] is not False or closeout["authorization_consumed"] is not True:
    raise SystemExit("AION-210-KI-0004 closeout lifecycle mismatch")

auth = json.loads((ROOT / "docs/knowledge-intelligence/authorization-ledger.json").read_text())
closed = [
    item
    for item in auth["records"]
    if item.get("authorization_transaction_id") == mesh.PARENT_AUTHORIZATION_ID
]
if len(closed) != 1:
    raise SystemExit("AION-210-KI-0004 authorization record missing")
if closed[0]["authorization_active"] is not False or closed[0]["authorization_consumed"] is not True:
    raise SystemExit("AION-210-KI-0004 must be closed and consumed")
if closed[0]["authorization_expired"] is not True or closed[0]["authorization_reusable"] is not False:
    raise SystemExit("AION-210-KI-0004 must be expired and non-reusable")
PY

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi

echo "knowledge intelligence domain expert mesh authorization PASS"
