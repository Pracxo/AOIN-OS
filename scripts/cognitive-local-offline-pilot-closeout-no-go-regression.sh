#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" scripts/lib/cognitive_architecture_governance.py \
  --repo-root "$ROOT_DIR" \
  --mode local-offline-pilot-closeout-no-go

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

cat <<'SUMMARY'
cognitive local-offline pilot closeout no-go result:
- active_cognitive_implementation_authorization_count=0
- production_cognitive_runtime_enabled=false
- production_event_subscription_enabled=false
- production_input=false
- user_traffic=false
- api_route_added=false
- kernel_registration_added=false
- startup_registration_added=false
- scheduler_started=false
- background_loop_added=false
- cli_installation=false
- network_calls=0
- connector_calls=0
- model_provider_calls=0
- credential_access=false
- source_mutations=0
- source_rewrite_runtime_enabled=false
- git_operations=0
- pull_requests_created_by_runtime=0
- approval_creation=0
- automatic_merge_enabled=false
- production_canary_enabled=false
- production_deployment_enabled=false
- model_weight_training_enabled=false
- consequential_action_execution=0
- package_files=absent
- migrations=absent
cognitive local-offline pilot closeout no-go PASS
SUMMARY
