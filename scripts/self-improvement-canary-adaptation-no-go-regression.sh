#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"
source "$ROOT_DIR/scripts/lib/python-selection.sh"

PYTHON_BIN="$(aion_select_brain_python "$ROOT_DIR")"
aion_verify_brain_python_test_dependencies "$PYTHON_BIN"

"$PYTHON_BIN" - <<'PY'
from __future__ import annotations

from aion_brain.self_improvement import (
    CANARY_RUNTIME_ENABLED,
    PRODUCTION_EXPOSURE_ENABLED,
    ROLLBACK_TRIGGERS,
    CanaryExposureBudget,
    CanaryMetricThreshold,
    CanaryPlan,
    PreferenceDistribution,
    ProceduralSkillRecord,
    StrategySelectionPolicy,
)


def expect_rejected(label: str, fn) -> None:
    try:
        fn()
    except Exception:
        return
    raise AssertionError(f"{label} must be rejected")


assert CANARY_RUNTIME_ENABLED is False
assert PRODUCTION_EXPOSURE_ENABLED is False
assert set(ROLLBACK_TRIGGERS) == {
    "policy_violation",
    "security_regression",
    "task_success_degradation",
    "user_correction_increase",
    "latency_budget_breach",
    "error_rate_increase",
    "benchmark_drift",
    "unexpected_runtime_effect",
}

expect_rejected(
    "production canary exposure",
    lambda: CanaryExposureBudget(
        budget_id="bad-budget",
        max_exposure_percentage=5.0,
        max_subjects=10,
        max_duration_minutes=30,
        production_exposure_enabled=True,
    ),
)

budget = CanaryExposureBudget(
    budget_id="budget-174-no-go",
    max_exposure_percentage=5.0,
    max_subjects=10,
    max_duration_minutes=30,
)
metric_threshold = CanaryMetricThreshold(
    metric_name="task_success",
    threshold=0.8,
    higher_is_better=True,
    rollback_trigger="task_success_degradation",
)
expect_rejected(
    "canary runtime activation",
    lambda: CanaryPlan(
        plan_id="bad-plan",
        proposal_id="proposal-174",
        merge_commit_sha="a" * 40,
        deployment_artifact_fingerprint="d" * 64,
        exposure_budget=budget,
        monitoring_duration_minutes=30,
        rollback_commit_sha="c" * 40,
        metric_thresholds=(metric_threshold,),
        metric_threshold_fingerprint="e" * 64,
        canary_runtime_enabled=True,
    ),
)
expect_rejected(
    "runtime strategy creation",
    lambda: StrategySelectionPolicy(
        allowlisted_strategy_ids=("safe-retry",),
        strategy_creation_at_runtime_enabled=True,
    ),
)
expect_rejected(
    "safety gate bypass",
    lambda: StrategySelectionPolicy(
        allowlisted_strategy_ids=("safe-retry",),
        safety_gate_bypass_enabled=True,
    ),
)
expect_rejected(
    "high-impact preference approval bypass",
    lambda: PreferenceDistribution(
        distribution_id="preference-174",
        user_scope_id="user-local",
        preference_key="concise_status",
        high_impact_approval_required=False,
    ),
)
expect_rejected(
    "procedural skill direct runtime activation",
    lambda: ProceduralSkillRecord(
        skill_id="skill-174",
        version=1,
        status="candidate",
        procedure_steps=("observe", "report"),
        policy_gate_passed=False,
        direct_runtime_activation_enabled=True,
    ),
)

print("self-improvement canary adaptation disabled-default checks PASS")
PY

if git tag --list 'v0.2*' 'aion-v0.2*' | grep -q .; then
  echo "v0.2 tag exists" >&2
  exit 1
fi

if gh release view v0.2 >/dev/null 2>&1 || gh release view aion-v0.2 >/dev/null 2>&1; then
  echo "v0.2 release exists" >&2
  exit 1
fi

cat <<'SUMMARY'
self-improvement canary adaptation no-go result:
- canary_runtime_enabled=false
- production_exposure_enabled=false
- production_canary_enabled=false
- automatic rollback: approval-threshold bound
- adaptive learning: data-only, bounded, and approval-gated
- runtime strategy creation=false
- safety gate bypass=false
- direct procedural skill activation=false
- model_weight_training_enabled=false
self-improvement canary adaptation no-go PASS
SUMMARY
