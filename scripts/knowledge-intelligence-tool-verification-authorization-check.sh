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

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-tool-verification-authorization-no-go-regression.sh

json_files=(
  examples/knowledge-intelligence/domain-expert-mesh-operator-evaluation-report.json
  examples/knowledge-intelligence/domain-expert-mesh-evaluation-scenario-summary.json
  examples/knowledge-intelligence/tool-verification-authorization.json
  examples/knowledge-intelligence/tool-capability-manifest.json
  examples/knowledge-intelligence/tool-intent.json
  examples/knowledge-intelligence/tool-invocation-plan.json
  examples/knowledge-intelligence/tool-plan-step.json
  examples/knowledge-intelligence/tool-expected-effect.json
  examples/knowledge-intelligence/tool-verification-rule.json
  examples/knowledge-intelligence/tool-simulation-result.json
  examples/knowledge-intelligence/tool-verification-finding.json
  examples/knowledge-intelligence/tool-attestation.json
  examples/knowledge-intelligence/tool-verification-session.json
  examples/knowledge-intelligence/tool-verification-resource-budget.json
  examples/knowledge-intelligence/tool-verification-runtime-hold.json
  examples/knowledge-intelligence/tool-verification-operator-review-item.json
  operator-console-static/demo-data/knowledge-intelligence-domain-expert-mesh-evaluation.json
  operator-console-static/demo-data/knowledge-intelligence-tool-verification-authorization.json
  operator-console-static/demo-data/knowledge-intelligence-tool-manifest.json
  operator-console-static/demo-data/knowledge-intelligence-tool-plan.json
  operator-console-static/demo-data/knowledge-intelligence-tool-simulation.json
  operator-console-static/demo-data/knowledge-intelligence-tool-attestation.json
  operator-console-static/demo-data/knowledge-intelligence-tool-verification-runtime-hold.json
)
for path in "${json_files[@]}"; do
  "$PYTHON_BIN" -m json.tool "$path" >/dev/null
done

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import importlib.util
import os
from pathlib import Path

ROOT = Path(os.environ["AION_REPO_ROOT"])
module_path = ROOT / "scripts/lib/knowledge_intelligence_tool_verification_authorization.py"
spec = importlib.util.spec_from_file_location("tool_auth", module_path)
assert spec is not None and spec.loader is not None
tool_auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool_auth)
tool_auth.validate_authorization_files(ROOT)
PY

if is_nested_gate_context; then
  echo "PASS: focused AION-215 pytest deferred to outer gate"
else
  "$PYTHON_BIN" -m pytest \
    services/brain-api/tests/test_knowledge_tool_verification_fabric.py \
    services/brain-api/tests/test_knowledge_tool_verification_attestation_spec.py \
    services/brain-api/tests/test_knowledge_tool_verification_scope_spec.py \
    services/brain-api/tests/test_knowledge_tool_verification_threat_model.py \
    services/brain-api/tests/test_knowledge_intelligence_current_projection.py \
    -q
fi

./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

aion_confirm_immutable_v01_tag_history >/dev/null
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

echo "knowledge intelligence tool verification authorization PASS"
