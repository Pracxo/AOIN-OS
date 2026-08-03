#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_KI_PROGRAM_COMPLETE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_KI_PROGRAM_FINAL_EVALUATION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

./scripts/knowledge-intelligence-program-complete-check.sh

if rg -n '(public_network_fetch_enabled": true|unrestricted_network_access_enabled": true|background_network_access_enabled": true|scheduled_public_research_enabled": true|background_crawler_enabled": true|automatic_verified_knowledge_promotion_enabled": true|persistent_verified_knowledge_write_enabled": true|cognitive_memory_write_enabled": true|belief_mutation_enabled": true|production_exposure": true)' docs/knowledge-intelligence examples/knowledge-intelligence operator-console-static/demo-data; then
  echo "ERROR: final program runtime boundary violated" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -v '^aion-v0\.2\.0-rc\.1$' | rg -n '.+'; then
  echo "ERROR: v0.2 tag exists" >&2
  exit 1
fi
if command -v gh >/dev/null 2>&1; then
  if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
    echo "ERROR: v0.2 release exists" >&2
    exit 1
  fi
fi

if is_nested_gate_context; then
  echo "PASS: full repository check deferred to outer gate"
else
  AION_AGGREGATE_GATE_RUNNING=1 ./scripts/check.sh
fi

echo "knowledge intelligence program complete runtime hold PASS"
