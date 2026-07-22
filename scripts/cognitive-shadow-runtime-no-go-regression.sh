#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode shadow-runtime-no-go

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

cat <<'SUMMARY'
cognitive shadow-runtime no-go result:
- production_cognitive_runtime_enabled=false
- api_route_added=false
- kernel_registration_added=false
- startup_registration_added=false
- scheduler_started=false
- background_loop_added=false
- cli_installation_added=false
- production_input=false
- user_traffic=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- source_rewrite=false
- git_mutation=false
- real_pull_request_creation=0
- approval_creation=0
- merge_operations=0
- deployment_operations=0
- production_canary=0
- model_weight_training=0
- consequential_action_execution=0
- package_files=absent
- migrations=absent
cognitive shadow-runtime no-go PASS
SUMMARY
