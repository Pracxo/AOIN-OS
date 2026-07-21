#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

for file in \
  examples/self-improvement/shadow-activation-authorization.json \
  examples/self-improvement/shadow-activation-candidate.json \
  examples/self-improvement/shadow-activation-request.json \
  examples/self-improvement/shadow-activation-approval-binding.json \
  examples/self-improvement/shadow-activation-resource-budget.json \
  examples/self-improvement/shadow-activation-monitoring-plan.json \
  examples/self-improvement/shadow-activation-deactivation-plan.json \
  examples/self-improvement/shadow-activation-runtime-hold.json \
  operator-console-static/demo-data/self-improvement-shadow-activation-authorization.json \
  operator-console-static/demo-data/self-improvement-shadow-activation-runtime-hold.json; do
  test -f "$file" || {
    echo "missing AION-180 JSON artifact: $file" >&2
    exit 1
  }
  "$PYTHON_BIN" -m json.tool "$file" >/dev/null
done

grep -q "0165-controlled-shadow-activation-control-plane-authorization.md" docs/adr/README.md || {
  echo "ADR 0165 is not indexed" >&2
  exit 1
}

./scripts/self-improvement-shadow-activation-authorization-no-go-regression.sh

"$PYTHON_BIN" scripts/lib/self_improvement_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-activation-authorization

"$PYTHON_BIN" -m pytest \
  services/brain-api/tests/test_self_improvement_shadow_activation_authorization_docs.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_authorization_validator.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_scope_spec.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_approval_binding_spec.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_budget_spec.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_monitoring_spec.py \
  services/brain-api/tests/test_self_improvement_shadow_activation_threat_model.py \
  -q

AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-operator-evaluation-check.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-shadow-mode-runtime-hold.sh
AION_AGGREGATE_GATE_RUNNING=1 ./scripts/self-improvement-final-check.sh
./scripts/docs-check.sh
./scripts/final-docs-audit.sh
./scripts/verify-no-domain-drift.sh
./scripts/boundary-check.sh

CONTROL_PLANE_STAGE="$("$PYTHON_BIN" - <<'PY'
from __future__ import annotations

import json
from pathlib import Path

ledger = json.loads(Path("docs/self-improvement/authorization-ledger.json").read_text())
print(ledger.get("current_stage", ""))
PY
)"

for path in \
  services/brain-api/src/aion_brain/contracts/self_improvement_shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_policy.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_approval.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_monitoring.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_deactivation.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_evidence.py \
  services/brain-api/src/aion_brain/self_improvement/shadow_activation_simulator.py; do
  if [[ "$CONTROL_PLANE_STAGE" == "shadow_activation_control_plane_implemented_disabled_pending_closeout" || \
        "$CONTROL_PLANE_STAGE" == "shadow_activation_control_plane_operator_evaluation_passed_disabled" || \
        "$CONTROL_PLANE_STAGE" == "shadow_activation_control_plane_operator_evaluation_failed_disabled" ]]; then
    test -f "$path" || {
      echo "AION-181 activation source must exist after implementation: $path" >&2
      exit 1
    }
  else
    test ! -e "$path" || {
      echo "AION-181 runtime source must be absent in AION-180: $path" >&2
      exit 1
    }
  fi
done

aion_confirm_immutable_v01_tag_history >/dev/null

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

echo "self improvement shadow activation authorization PASS"
