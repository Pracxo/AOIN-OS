#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode persistent-state-closeout-no-go

cat <<'SUMMARY'
cognitive persistent-state closeout no-go result:
- runtime_effect=false
- api_route_added=false
- kernel_registration_added=false
- background_loop_added=false
- action_execution_enabled=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- model_weight_training=0
- package_files=absent
- migrations=absent
cognitive persistent-state closeout no-go PASS
SUMMARY
