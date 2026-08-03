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
  [[ "${AION_PUBLIC_RESEARCH_PILOT_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_PUBLIC_RESEARCH_PILOT_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}
if is_nested_gate_context; then
  echo "PASS: implementation check running in outer context; authorization gate retained"
  ./scripts/knowledge-intelligence-public-research-pilot-authorization-check.sh
else
  AION_PUBLIC_RESEARCH_PILOT_RUNTIME_HOLD_SKIP_FULL_CHECK=1 ./scripts/knowledge-intelligence-public-research-pilot-check.sh
fi
PYTHONPATH="$ROOT_DIR/scripts/lib:${PYTHONPATH:-}" "$PYTHON_BIN" - <<'PY'
from __future__ import annotations
import os
from pathlib import Path
import knowledge_intelligence_public_research_pilot_authorization as auth
auth.validate_runtime_hold(Path(os.environ["AION_REPO_ROOT"]))
PY
aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then echo "ERROR: v0.2 tag exists" >&2; exit 1; fi
if is_nested_gate_context; then echo "PASS: full repository check deferred to outer gate"; else AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh; fi
echo "knowledge intelligence public research pilot runtime hold PASS"
