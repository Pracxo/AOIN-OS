"""Deterministic counterfactual evaluation for shadow overlays."""

from __future__ import annotations

from decimal import Decimal

from aion_brain.contracts.governed_engagement_learning import (
    METRIC_DIRECTIONS,
    ZERO,
    EngagementCounterfactualCase,
    EngagementCounterfactualOutcome,
    EngagementCounterfactualRecommendation,
    EngagementCounterfactualResult,
    EngagementMetricDelta,
    EngagementMetricDirection,
    EngagementOverlaySnapshot,
    build_record,
)


def build_counterfactual_case(
    *,
    case_id: str,
    target_component_code: str,
    target_policy_code: str,
    input_codes: tuple[str, ...],
    hard_gate_codes: tuple[str, ...] = (),
) -> EngagementCounterfactualCase:
    payload = {
        "schema_version": "aion-glm-engagement-counterfactual-case/v1",
        "case_id": case_id,
        "target_component_code": target_component_code,
        "target_policy_code": target_policy_code,
        "input_codes": tuple(sorted(input_codes)),
        "baseline_expected_codes": ("baseline-retained",),
        "hard_gate_codes": tuple(sorted(hard_gate_codes)),
        "metric_registry": tuple(sorted(METRIC_DIRECTIONS)),
        "synthetic_or_redacted": True,
        "raw_user_message_present": False,
        "read_only": True,
    }
    return build_record(EngagementCounterfactualCase, payload, "case_fingerprint")


class DeterministicEngagementShadowAdapter:
    """Closed-registry reference adapter for shadow semantics only."""

    def evaluate(
        self,
        *,
        case: EngagementCounterfactualCase,
        overlay_snapshot: EngagementOverlaySnapshot | None,
    ) -> EngagementCounterfactualOutcome:
        active = overlay_snapshot is not None and overlay_snapshot.record_count > 0
        metrics: dict[str, Decimal] = {
            "task_completion": Decimal("0.500000") + (Decimal("0.100000") if active else ZERO),
            "retrieval_success": Decimal("0.500000") + (Decimal("0.100000") if active else ZERO),
            "source_diversity": Decimal("0.500000") + (Decimal("0.100000") if active else ZERO),
            "citation_completeness": Decimal("0.500000")
            + (Decimal("0.100000") if active else ZERO),
            "abstention_correctness": Decimal("1.000000"),
            "routing_consistency": Decimal("0.500000")
            + (Decimal("0.100000") if active else ZERO),
            "verification_coverage": Decimal("0.500000")
            + (Decimal("0.100000") if active else ZERO),
            "response_format_compliance": Decimal("1.000000"),
            "clarification_count": Decimal("1.000000")
            - (Decimal("0.100000") if active else ZERO),
            "latency": Decimal("1.000000") + (Decimal("0.010000") if active else ZERO),
            "bounded_resource_cost": Decimal("1.000000")
            + (Decimal("0.010000") if active else ZERO),
            "policy_violations": ZERO,
            "safety_violations": ZERO,
        }
        payload = {
            "outcome_id": f"outcome-{case.case_id}-{'candidate' if active else 'baseline'}",
            "outcome_codes": (
                "shadow-overlay-evaluated" if active else "baseline-retained",
            ),
            "metrics": metrics,
            "safety_violations": 0,
            "policy_violations": 0,
            "runtime_effect": False,
        }
        return build_record(
            EngagementCounterfactualOutcome,
            payload,
            "outcome_fingerprint",
        )


def calculate_metric_delta(
    *,
    metric_name: str,
    baseline_value: Decimal,
    candidate_value: Decimal,
) -> EngagementMetricDelta:
    direction = METRIC_DIRECTIONS[metric_name]
    delta = candidate_value - baseline_value
    if direction is EngagementMetricDirection.HIGHER_IS_BETTER:
        improved = candidate_value > baseline_value
        regressed = candidate_value < baseline_value
    elif direction is EngagementMetricDirection.LOWER_IS_BETTER:
        improved = candidate_value < baseline_value
        regressed = candidate_value > baseline_value
    else:
        improved = candidate_value == ZERO
        regressed = candidate_value != ZERO
    payload = {
        "schema_version": "aion-glm-engagement-metric-delta/v1",
        "metric_name": metric_name,
        "direction": direction,
        "baseline_value": baseline_value,
        "candidate_value": candidate_value,
        "delta": delta,
        "improved": improved,
        "regressed": regressed,
        "hard_gate": direction is EngagementMetricDirection.ZERO_REQUIRED,
    }
    return build_record(EngagementMetricDelta, payload, "metric_fingerprint")


def evaluate_counterfactual_case(
    *,
    case: EngagementCounterfactualCase,
    overlay_snapshot: EngagementOverlaySnapshot,
    adapter: DeterministicEngagementShadowAdapter | None = None,
) -> EngagementCounterfactualResult:
    reference = adapter or DeterministicEngagementShadowAdapter()
    baseline = reference.evaluate(case=case, overlay_snapshot=None)
    candidate = reference.evaluate(case=case, overlay_snapshot=overlay_snapshot)
    deltas = tuple(
        calculate_metric_delta(
            metric_name=metric,
            baseline_value=baseline.metrics[metric],
            candidate_value=candidate.metrics[metric],
        )
        for metric in sorted(case.metric_registry)
    )
    safety_gate = candidate.safety_violations == 0
    policy_gate = candidate.policy_violations == 0
    reasons: tuple[str, ...]
    if not safety_gate:
        recommendation = EngagementCounterfactualRecommendation.REJECT_CANDIDATE
        reasons = ("engagement_safety_gate_failed", "engagement_reject_candidate")
    elif not policy_gate:
        recommendation = EngagementCounterfactualRecommendation.RETAIN_BASELINE
        reasons = ("engagement_policy_gate_failed", "engagement_retain_baseline")
    elif any(delta.regressed and delta.hard_gate for delta in deltas):
        recommendation = EngagementCounterfactualRecommendation.RETAIN_BASELINE
        reasons = ("engagement_retain_baseline",)
    elif any(delta.improved for delta in deltas):
        recommendation = EngagementCounterfactualRecommendation.APPROVE_SHADOW_CANDIDATE
        reasons = (
            "engagement_safety_gate_passed",
            "engagement_policy_gate_passed",
            "engagement_approve_shadow_candidate",
        )
    else:
        recommendation = EngagementCounterfactualRecommendation.RETAIN_BASELINE
        reasons = ("engagement_retain_baseline",)
    payload = {
        "schema_version": "aion-glm-engagement-counterfactual-result/v1",
        "case_id": case.case_id,
        "baseline_outcome_fingerprint": baseline.outcome_fingerprint,
        "candidate_outcome_fingerprint": candidate.outcome_fingerprint,
        "metric_deltas": deltas,
        "safety_gate_passed": safety_gate,
        "policy_gate_passed": policy_gate,
        "recommendation": recommendation,
        "reason_codes": reasons,
        "factual_effect": False,
        "confidence_effect": False,
        "knowledge_effect": False,
        "production_policy_effect": False,
        "runtime_effect": False,
    }
    return build_record(EngagementCounterfactualResult, payload, "result_fingerprint")


__all__ = [
    "DeterministicEngagementShadowAdapter",
    "build_counterfactual_case",
    "calculate_metric_delta",
    "evaluate_counterfactual_case",
]
