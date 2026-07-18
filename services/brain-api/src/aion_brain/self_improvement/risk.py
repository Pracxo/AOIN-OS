"""Risk assessment helpers for governed self-improvement."""

from __future__ import annotations

from aion_brain.contracts.self_improvement import (
    ImprovementRiskAssessment,
    ImprovementRiskLevel,
    utc_now,
)


def assess_improvement_risk(
    *,
    proposal_id: str,
    protected_core_impact: bool,
    safety_passed: bool,
    benchmark_passed: bool,
    quality_score: float,
    requested_risk_level: ImprovementRiskLevel | None = None,
    findings: tuple[str, ...] = (),
    evidence: dict[str, object] | None = None,
) -> ImprovementRiskAssessment:
    """Build a deterministic risk assessment without using quality to offset safety."""

    risk_level = requested_risk_level or ("high" if protected_core_impact else "medium")
    approval_eligible = safety_passed and benchmark_passed
    return ImprovementRiskAssessment(
        risk_assessment_id=f"{proposal_id}:risk",
        proposal_id=proposal_id,
        risk_level=risk_level,
        protected_core_impact=protected_core_impact,
        safety_passed=safety_passed,
        benchmark_passed=benchmark_passed,
        quality_score=quality_score,
        approval_eligible=approval_eligible,
        findings=findings,
        evidence=evidence or {},
        created_at=utc_now(),
    )

