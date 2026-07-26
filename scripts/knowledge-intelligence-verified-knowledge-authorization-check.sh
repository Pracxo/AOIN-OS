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
./scripts/knowledge-intelligence-verified-knowledge-authorization-no-go-regression.sh
json_files=(examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json examples/knowledge-intelligence/integrated-research-agent-evaluation-scenario-summary.json examples/knowledge-intelligence/integrated-knowledge-lineage.json examples/knowledge-intelligence/verified-knowledge-authorization.json examples/knowledge-intelligence/verified-knowledge-candidate.json examples/knowledge-intelligence/verified-knowledge-candidate-version.json examples/knowledge-intelligence/verified-knowledge-candidate-batch.json examples/knowledge-intelligence/verified-knowledge-memory-snapshot.json examples/knowledge-intelligence/verified-knowledge-candidate-query.json examples/knowledge-intelligence/verified-knowledge-candidate-integrity-report.json examples/knowledge-intelligence/verified-knowledge-operator-review-item.json examples/knowledge-intelligence/engagement-signal-metadata.json examples/knowledge-intelligence/engagement-learning-candidate.json examples/knowledge-intelligence/engagement-learning-candidate-batch.json examples/knowledge-intelligence/verified-knowledge-resource-budget.json examples/knowledge-intelligence/verified-knowledge-runtime-hold.json operator-console-static/demo-data/knowledge-intelligence-integrated-research-agent-evaluation.json operator-console-static/demo-data/knowledge-intelligence-integrated-lineage.json operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-authorization.json operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-candidate.json operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-versioning.json operator-console-static/demo-data/knowledge-intelligence-engagement-learning-candidate.json operator-console-static/demo-data/knowledge-intelligence-verified-knowledge-runtime-hold.json)
for path in "${json_files[@]}"; do "$PYTHON_BIN" -m json.tool "$path" >/dev/null; done
PYTHONPATH="$ROOT_DIR/scripts/lib:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import os
from pathlib import Path
import knowledge_intelligence_verified_knowledge_authorization as auth
auth.validate_authorization_files(Path(os.environ["AION_REPO_ROOT"]))
PY
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh
aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then echo "ERROR: v0.2 release exists" >&2; exit 1; fi
fi
echo "knowledge intelligence verified knowledge authorization PASS"
