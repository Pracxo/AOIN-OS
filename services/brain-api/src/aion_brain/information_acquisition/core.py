"""Offline active information-acquisition planning services."""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from datetime import UTC, datetime

from aion_brain.contracts.information_acquisition import (
    AcquisitionCost,
    AcquisitionRisk,
    CandidateStatus,
    ClarificationCandidate,
    ExpectedInformationGain,
    ExperimentCandidate,
    InformationAcquisitionEvidence,
    InformationAcquisitionPlan,
    InformationAcquisitionRuntimeBoundary,
    InformationCandidate,
    InformationNeed,
    InformationStoppingDecision,
    KnowledgeGap,
    ObservationCandidate,
    RetrievalCandidate,
    RiskSeverity,
    acquisition_replay_hash,
)

GENERATED_AT = datetime(1970, 1, 1, tzinfo=UTC)

PermissionMap = Mapping[str, bool]
ApprovedRefs = Mapping[str, tuple[str, ...]]


class KnowledgeGapDetector:
    """Detect decision-relevant uncertainty gaps from bounded information needs."""

    def detect(
        self,
        needs: Iterable[InformationNeed],
        *,
        minimum_uncertainty_delta: float = 0.05,
    ) -> tuple[KnowledgeGap, ...]:
        """Return deterministic knowledge gaps for reducible uncertainty."""

        gaps: list[KnowledgeGap] = []
        for need in sorted(needs, key=lambda item: item.need_id):
            delta = need.current_uncertainty - need.target_uncertainty
            if delta < minimum_uncertainty_delta or need.decision_relevance == 0:
                continue
            gaps.append(
                KnowledgeGap(
                    gap_id=f"gap-{need.need_id}",
                    need_id=need.need_id,
                    subject=need.subject,
                    current_uncertainty=need.current_uncertainty,
                    target_uncertainty=need.target_uncertainty,
                    uncertainty_delta=delta,
                    decision_relevance=need.decision_relevance,
                    rationale=(
                        "decision uncertainty exceeds target and can be reduced by "
                        "approved information asks"
                    ),
                    evidence_refs=need.evidence_refs,
                    created_at=GENERATED_AT,
                )
            )
        return tuple(gaps)


class ObservationCandidateGenerator:
    """Generate candidate asks without acquiring information."""

    def generate(
        self,
        gap: KnowledgeGap,
        *,
        permissions: PermissionMap | None = None,
        approved_refs: ApprovedRefs | None = None,
    ) -> tuple[InformationCandidate, ...]:
        """Return clarification, retrieval, observation, and synthetic experiment asks."""

        permission_map = permissions or {}
        refs = approved_refs or {}
        return (
            ClarificationCandidate(
                candidate_id=f"candidate-{gap.gap_id}-clarification",
                need_id=gap.need_id,
                gap_id=gap.gap_id,
                request_summary=f"Clarify {gap.subject}",
                clarification_question=(
                    f"What approved local evidence would reduce uncertainty about {gap.subject}?"
                ),
                recipient_role="operator",
                permission_granted=permission_map.get("clarification", False),
                status=_status(permission_map.get("clarification", False)),
                evidence_refs=(f"aion://information-acquisition/{gap.gap_id}",),
                created_at=GENERATED_AT,
            ),
            RetrievalCandidate(
                candidate_id=f"candidate-{gap.gap_id}-retrieval",
                need_id=gap.need_id,
                gap_id=gap.gap_id,
                request_summary=f"Retrieve approved evidence for {gap.subject}",
                retrieval_ref=f"aion://approved-retrieval/{gap.gap_id}",
                query_summary=f"Retrieve bounded local evidence for {gap.subject}",
                approved_source_refs=refs.get("retrieval", ()),
                permission_granted=permission_map.get("retrieval", False),
                status=_status(permission_map.get("retrieval", False)),
                evidence_refs=(f"aion://information-acquisition/{gap.gap_id}",),
                created_at=GENERATED_AT,
            ),
            ObservationCandidate(
                candidate_id=f"candidate-{gap.gap_id}-observation",
                need_id=gap.need_id,
                gap_id=gap.gap_id,
                request_summary=f"Observe approved local state for {gap.subject}",
                observation_scope=f"approved local observation for {gap.subject}",
                approved_observation_ref=_first_ref(refs.get("observation", ())),
                permission_granted=permission_map.get("observation", False),
                status=_status(permission_map.get("observation", False)),
                evidence_refs=(f"aion://information-acquisition/{gap.gap_id}",),
                created_at=GENERATED_AT,
            ),
            ExperimentCandidate(
                candidate_id=f"candidate-{gap.gap_id}-experiment",
                need_id=gap.need_id,
                gap_id=gap.gap_id,
                request_summary=f"Run synthetic comparison for {gap.subject}",
                experiment_design=f"synthetic uncertainty-reduction comparison for {gap.subject}",
                expected_observations=(f"bounded synthetic evidence about {gap.subject}",),
                permission_granted=permission_map.get("experiment", False),
                status=_status(permission_map.get("experiment", False)),
                evidence_refs=(f"aion://information-acquisition/{gap.gap_id}",),
                created_at=GENERATED_AT,
            ),
        )


class InformationGainEstimator:
    """Estimate expected uncertainty reduction for candidates."""

    _multipliers = {
        "clarification": 0.45,
        "retrieval": 0.70,
        "observation": 0.55,
        "experiment": 0.65,
    }
    _confidence = {
        "clarification": 0.80,
        "retrieval": 0.90,
        "observation": 0.84,
        "experiment": 0.82,
    }

    def estimate(
        self,
        candidate: InformationCandidate,
        gap: KnowledgeGap,
    ) -> ExpectedInformationGain:
        """Return deterministic expected information gain for one candidate."""

        reduction = min(
            gap.uncertainty_delta,
            gap.current_uncertainty * self._multipliers[candidate.candidate_type],
        )
        posterior = max(gap.target_uncertainty, gap.current_uncertainty - reduction)
        expected_gain = (gap.current_uncertainty - posterior) * gap.decision_relevance
        return ExpectedInformationGain(
            estimate_id=f"gain-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            gap_id=gap.gap_id,
            prior_uncertainty=gap.current_uncertainty,
            expected_posterior_uncertainty=posterior,
            decision_relevance=gap.decision_relevance,
            expected_information_gain=expected_gain,
            confidence=self._confidence[candidate.candidate_type],
            evidence_refs=(f"aion://information-acquisition/gain/{candidate.candidate_id}",),
            created_at=GENERATED_AT,
        )


class AcquisitionCostEvaluator:
    """Estimate bounded local cost without external calls."""

    _costs = {
        "clarification": (0.08, 0.08, 0.00),
        "retrieval": (0.10, 0.08, 0.04),
        "observation": (0.16, 0.12, 0.04),
        "experiment": (0.24, 0.16, 0.08),
    }

    def estimate(self, candidate: InformationCandidate) -> AcquisitionCost:
        """Return deterministic cost estimate for one candidate."""

        time_cost, attention_cost, resource_cost = self._costs[candidate.candidate_type]
        return AcquisitionCost(
            cost_id=f"cost-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            time_cost=time_cost,
            attention_cost=attention_cost,
            resource_cost=resource_cost,
            total_cost=min(1.0, time_cost + attention_cost + resource_cost),
            evidence_refs=(f"aion://information-acquisition/cost/{candidate.candidate_id}",),
            created_at=GENERATED_AT,
        )


class AcquisitionRiskEvaluator:
    """Fail closed when permission or approved references are missing."""

    _base_risks = {
        "clarification": (0.04, 0.03, 0.00),
        "retrieval": (0.08, 0.08, 0.00),
        "observation": (0.10, 0.06, 0.00),
        "experiment": (0.12, 0.04, 0.00),
    }

    def evaluate(self, candidate: InformationCandidate) -> AcquisitionRisk:
        """Return permission-bound risk metadata for a candidate."""

        safety_risk, privacy_risk, irreversible_risk = self._base_risks[
            candidate.candidate_type
        ]
        missing_reference = (
            isinstance(candidate, RetrievalCandidate)
            and candidate.permission_granted
            and not candidate.approved_source_refs
        )
        blocked = not candidate.permission_granted or missing_reference
        policy_risk = 1.0 if blocked else 0.0
        overall = max(safety_risk, privacy_risk, policy_risk, irreversible_risk)
        return AcquisitionRisk(
            risk_id=f"acqhazard-{candidate.candidate_id}",
            candidate_id=candidate.candidate_id,
            severity=_severity(overall),
            safety_risk=safety_risk,
            privacy_risk=privacy_risk,
            policy_risk=policy_risk,
            irreversible_risk=irreversible_risk,
            overall_risk=overall,
            permission_granted=candidate.permission_granted,
            blocked=blocked,
            rationale=(
                "permission or approved reference missing; candidate blocked"
                if blocked
                else "permission and local safety checks passed"
            ),
            evidence_refs=(f"aion://information-acquisition/risk/{candidate.candidate_id}",),
            created_at=GENERATED_AT,
        )


class ClarificationPolicy:
    """Select low-risk clarification asks when additional permission is required."""

    def clarification_candidates(
        self,
        candidates: Iterable[InformationCandidate],
    ) -> tuple[ClarificationCandidate, ...]:
        """Return clarification candidates in deterministic order."""

        return tuple(
            sorted(
                (
                    candidate
                    for candidate in candidates
                    if isinstance(candidate, ClarificationCandidate)
                ),
                key=lambda item: item.candidate_id,
            )
        )


class InformationStoppingPolicy:
    """Apply the expected value versus cost and risk stopping rule."""

    def decide(
        self,
        *,
        plan_id: str,
        selected_candidate_ids: tuple[str, ...],
        gain_estimates: tuple[ExpectedInformationGain, ...],
        costs: tuple[AcquisitionCost, ...],
        risks: tuple[AcquisitionRisk, ...],
    ) -> InformationStoppingDecision:
        """Return whether acquisition planning should continue."""

        selected = set(selected_candidate_ids)
        expected_value = _bounded_sum(
            estimate.expected_information_gain
            for estimate in gain_estimates
            if estimate.candidate_id in selected
        )
        total_cost = _bounded_sum(
            cost.total_cost for cost in costs if cost.candidate_id in selected
        )
        total_risk = _bounded_sum(
            risk.overall_risk for risk in risks if risk.candidate_id in selected
        )
        continue_acquisition = bool(selected_candidate_ids) and expected_value > (
            total_cost + total_risk
        )
        selected_ids = selected_candidate_ids if continue_acquisition else ()
        return InformationStoppingDecision(
            decision_id=f"stopping-{plan_id}",
            plan_id=plan_id,
            continue_acquisition=continue_acquisition,
            reason=(
                "expected information gain exceeds bounded cost and risk"
                if continue_acquisition
                else "expected information gain does not justify cost and risk"
            ),
            selected_candidate_ids=selected_ids,
            expected_value=expected_value,
            total_cost=total_cost,
            total_risk=total_risk,
            stopped_because_value_below_cost=not continue_acquisition,
            evidence_refs=(f"aion://information-acquisition/stopping/{plan_id}",),
            created_at=GENERATED_AT,
        )


class InformationAcquisitionPlanner:
    """Create permission-bound information request plans without acquisition."""

    def __init__(
        self,
        *,
        gap_detector: KnowledgeGapDetector | None = None,
        candidate_generator: ObservationCandidateGenerator | None = None,
        gain_estimator: InformationGainEstimator | None = None,
        cost_evaluator: AcquisitionCostEvaluator | None = None,
        risk_evaluator: AcquisitionRiskEvaluator | None = None,
        clarification_policy: ClarificationPolicy | None = None,
        stopping_policy: InformationStoppingPolicy | None = None,
    ) -> None:
        self._gap_detector = gap_detector or KnowledgeGapDetector()
        self._candidate_generator = candidate_generator or ObservationCandidateGenerator()
        self._gain_estimator = gain_estimator or InformationGainEstimator()
        self._cost_evaluator = cost_evaluator or AcquisitionCostEvaluator()
        self._risk_evaluator = risk_evaluator or AcquisitionRiskEvaluator()
        self._clarification_policy = clarification_policy or ClarificationPolicy()
        self._stopping_policy = stopping_policy or InformationStoppingPolicy()

    def rank_candidates(
        self,
        *,
        gap: KnowledgeGap,
        permissions: PermissionMap | None = None,
        approved_refs: ApprovedRefs | None = None,
    ) -> tuple[
        tuple[
            InformationCandidate,
            ExpectedInformationGain,
            AcquisitionCost,
            AcquisitionRisk,
            float,
        ],
        ...,
    ]:
        """Return candidates sorted by expected value margin and stable id."""

        candidates = self._candidate_generator.generate(
            gap,
            permissions=permissions,
            approved_refs=approved_refs,
        )
        scored = []
        for candidate in candidates:
            gain = self._gain_estimator.estimate(candidate, gap)
            cost = self._cost_evaluator.estimate(candidate)
            risk = self._risk_evaluator.evaluate(candidate)
            margin = (
                gain.expected_information_gain
                - cost.total_cost
                - risk.overall_risk
            )
            scored.append((candidate, gain, cost, risk, margin))
        return tuple(
            sorted(
                scored,
                key=lambda item: (
                    item[3].blocked,
                    -item[4],
                    item[0].candidate_id,
                ),
            )
        )

    def create_plan(
        self,
        *,
        need: InformationNeed,
        permissions: PermissionMap | None = None,
        approved_refs: ApprovedRefs | None = None,
        plan_id: str = "information-acquisition-plan",
    ) -> InformationAcquisitionPlan:
        """Create a deterministic active information-acquisition plan."""

        gaps = self._gap_detector.detect((need,))
        if not gaps:
            raise ValueError("no decision-relevant knowledge gap is available")
        gap = gaps[0]
        ranked = self.rank_candidates(
            gap=gap,
            permissions=permissions,
            approved_refs=approved_refs,
        )
        candidates = tuple(item[0] for item in ranked)
        gains = tuple(item[1] for item in ranked)
        costs = tuple(item[2] for item in ranked)
        risks = tuple(item[3] for item in ranked)
        selected_candidate_ids = tuple(
            candidate.candidate_id
            for candidate, _gain, _cost, risk, margin in ranked
            if margin > 0 and candidate.permission_granted and not risk.blocked
        )
        stopping_decision = self._stopping_policy.decide(
            plan_id=plan_id,
            selected_candidate_ids=selected_candidate_ids[:1],
            gain_estimates=gains,
            costs=costs,
            risks=risks,
        )
        replay_hash = acquisition_replay_hash(
            {
                "plan_id": plan_id,
                "need": need,
                "gaps": gaps,
                "candidates": tuple(candidate.fingerprint for candidate in candidates),
                "gains": tuple(gain.fingerprint for gain in gains),
                "costs": tuple(cost.fingerprint for cost in costs),
                "risks": tuple(risk.fingerprint for risk in risks),
                "selected_candidate_ids": stopping_decision.selected_candidate_ids,
            }
        )
        evidence = InformationAcquisitionEvidence(
            evidence_id=f"information-acquisition-evidence-{plan_id}",
            plan_id=plan_id,
            uncertainty_detection_count=len(gaps),
            runtime_boundary=InformationAcquisitionRuntimeBoundary(
                boundary_id=f"information-acquisition-boundary-{plan_id}",
                created_at=GENERATED_AT,
            ),
            evidence_refs=(
                f"aion://information-acquisition/{plan_id}",
                f"aion://information-acquisition/replay/{replay_hash}",
            ),
            created_at=GENERATED_AT,
        )
        return InformationAcquisitionPlan(
            plan_id=plan_id,
            need=need,
            gaps=gaps,
            candidates=candidates,
            gain_estimates=gains,
            costs=costs,
            risks=risks,
            selected_candidate_ids=stopping_decision.selected_candidate_ids,
            stopping_decision=stopping_decision,
            evidence=evidence,
            created_at=GENERATED_AT,
        )

    def clarification_items(
        self,
        plan: InformationAcquisitionPlan,
    ) -> tuple[ClarificationCandidate, ...]:
        """Return clarification asks from a plan without asking them."""

        return self._clarification_policy.clarification_candidates(plan.candidates)


def _status(permission_granted: bool) -> CandidateStatus:
    return "approved" if permission_granted else "proposed"


def _first_ref(values: tuple[str, ...]) -> str | None:
    return values[0] if values else None


def _severity(overall_risk: float) -> RiskSeverity:
    if overall_risk >= 0.9:
        return "critical"
    if overall_risk >= 0.5:
        return "high"
    if overall_risk >= 0.2:
        return "medium"
    return "low"


def _bounded_sum(values: Iterable[float]) -> float:
    return min(1.0, max(0.0, sum(values)))


__all__ = [
    "AcquisitionCostEvaluator",
    "AcquisitionRiskEvaluator",
    "ClarificationPolicy",
    "GENERATED_AT",
    "InformationAcquisitionPlanner",
    "InformationGainEstimator",
    "InformationStoppingPolicy",
    "KnowledgeGapDetector",
    "ObservationCandidateGenerator",
]
