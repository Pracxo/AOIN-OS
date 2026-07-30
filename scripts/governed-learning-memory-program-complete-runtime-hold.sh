#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/immutable-tags.sh"
source "$ROOT_DIR/scripts/lib/portable-search.sh"

is_nested_gate_context() {
  [[ -n "${PYTEST_CURRENT_TEST:-}" ]] && return 0
  [[ "${AION_GLM_PROGRAM_COMPLETE_RUNTIME_HOLD_SKIP_FULL_CHECK:-}" == "1" ]] && return 0
  [[ "${AION_GLM_PROGRAM_FINAL_EVALUATION_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_GLM_PROGRAM_COMPLETE_CHECK_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_AGGREGATE_GATE_RUNNING:-}" == "1" ]] && return 0
  [[ "${AION_CHECK_RUNNING:-}" == "1" ]] && return 0
  return 1
}

export AION_GLM_PROGRAM_COMPLETE_CHECK_RUNNING=1
./scripts/governed-learning-memory-program-complete-check.sh

if rg -n '(production_runtime_authorized": true|repeat_live_pilot_authorized": true|active_continual_learning_execution_authorization": true|operator_invoked_continual_learning_pilot_available": true|background_continual_learning_enabled": true|scheduled_continual_learning_enabled": true|automatic_cycle_continuation_enabled": true|automatic_source_discovery_enabled": true|web_crawler_enabled": true|automatic_candidate_approval_enabled": true|automatic_knowledge_promotion_enabled": true|automatic_persistence_enabled": true|retained_pilot_store_enabled": true|production_memory_write_enabled": true|production_policy_mutation_enabled": true|cognitive_memory_write_enabled": true|actual_belief_creation_enabled": true|actual_belief_mutation_enabled": true|self_rewrite_enabled": true|runtime_source_rewrite_enabled": true|model_weight_training_enabled": true|production_exposure": true)' docs/governed-learning-memory docs/release examples/governed-learning-memory operator-console-static/demo-data; then
  echo "ERROR: final GLM runtime boundary violated" >&2
  exit 1
fi

aion_confirm_immutable_v01_tag_history >/dev/null
if git tag --list 'v0.2*' 'aion-v0.2*' | rg -n '.+'; then
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

echo "governed learning memory program complete runtime hold PASS"
