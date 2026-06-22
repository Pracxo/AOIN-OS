"""Deterministic Brain trace evaluator."""

from datetime import UTC, datetime

from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.traces import DecisionTrace


class Evaluator:
    """Score decision traces with deterministic heuristics."""

    def evaluate(self, trace: DecisionTrace) -> EvaluationRecord:
        """Create a bounded evaluation record without model grading."""
        status = str(trace.outcome.get("status", "unknown"))
        scores = {
            "goal_completion_score": _goal_completion_score(trace, status),
            "context_quality_score": 1.0 if trace.context_id else 0.25,
            "memory_relevance_score": _memory_relevance_score(trace),
            "plan_quality_score": _plan_quality_score(trace, status),
            "policy_compliance_score": _policy_compliance_score(trace, status),
            "execution_readiness_score": _execution_readiness_score(trace, status),
            "reasoning_quality_score": _reasoning_quality_score(trace, status),
            "lifecycle_readiness_score": _lifecycle_readiness_score(trace, status),
            "evidence_grounding_score": _evidence_grounding_score(trace, status),
        }
        return EvaluationRecord(
            evaluation_id=f"evaluation-{trace.trace_id}",
            trace_id=trace.trace_id,
            scores=scores,
            lessons=_lessons(trace, scores, status),
            created_at=datetime.now(UTC),
        )


def _goal_completion_score(trace: DecisionTrace, status: str) -> float:
    if status == "planned" and trace.plan_id:
        return 0.8
    if status == "blocked_by_policy":
        return 0.5
    return 0.2


def _memory_relevance_score(trace: DecisionTrace) -> float:
    return 0.8 if trace.memory_refs else 0.6


def _plan_quality_score(trace: DecisionTrace, status: str) -> float:
    if trace.plan_id:
        return 0.85 if status == "planned" else 0.7
    if trace.intent_id:
        return 0.2
    return 0.1


def _policy_compliance_score(trace: DecisionTrace, status: str) -> float:
    if status == "blocked_by_policy":
        return 0.95
    if trace.policy_decisions:
        return 0.9
    return 0.4


def _execution_readiness_score(trace: DecisionTrace, status: str) -> float:
    if not trace.plan_id or status == "blocked_by_policy":
        return 0.0
    if trace.outcome.get("execution_ready") is True:
        return 1.0
    if trace.outcome.get("execution_approval_required") is True:
        return 0.5
    return 0.0


def _reasoning_quality_score(trace: DecisionTrace, status: str) -> float:
    confidence = trace.outcome.get("reasoning_confidence")
    if status == "blocked_by_policy" and (
        confidence is None or (isinstance(confidence, int | float) and float(confidence) <= 0.0)
    ):
        return 0.0
    if trace.outcome.get("reasoning_requires_clarification") is True:
        return 0.6
    if isinstance(confidence, int | float) and float(confidence) >= 0.8:
        return 1.0
    if trace.reasoning_refs:
        return 0.5
    return 0.0


def _lifecycle_readiness_score(trace: DecisionTrace, status: str) -> float:
    if status == "blocked_by_policy":
        return 0.0
    if trace.outcome.get("reasoning_requires_clarification") is True:
        return 0.3
    if trace.plan_id and trace.outcome.get("can_create_task") is True:
        return 1.0
    if trace.outcome.get("can_create_goal") is True:
        return 0.7
    return 0.0


def _evidence_grounding_score(trace: DecisionTrace, status: str) -> float:
    claims = trace.outcome.get("grounding_claims")
    if isinstance(claims, list) and claims:
        statuses = [claim.get("verification_status") for claim in claims if isinstance(claim, dict)]
        if any(value == "supported" for value in statuses):
            return 1.0
        if statuses and all(value == "insufficient_evidence" for value in statuses):
            return 0.0 if trace.outcome.get("final_output_claims_completion") is True else 0.3
    evidence_refs = trace.outcome.get("evidence_refs")
    if isinstance(evidence_refs, list) and any(isinstance(ref, str) for ref in evidence_refs):
        return 0.7
    if status == "planned":
        return 0.3
    return 0.0


def _lessons(trace: DecisionTrace, scores: dict[str, float], status: str) -> list[str]:
    lessons: list[str] = []
    if not trace.memory_refs:
        lessons.append("memory_recall_was_empty")
    if scores["plan_quality_score"] < 0.5:
        lessons.append("planning_needs_clearer_context")
    if status == "blocked_by_policy":
        lessons.append("policy_block_was_preserved")
    if scores["reasoning_quality_score"] == 0.0 and trace.reasoning_refs:
        lessons.append("reasoning_was_blocked_or_failed")
    if scores.get("lifecycle_readiness_score", 0.0) >= 1.0:
        lessons.append("plan_can_be_converted_to_task")
    if scores.get("evidence_grounding_score", 0.0) < 0.5:
        lessons.append("evidence_grounding_needs_source_support")
    if not lessons:
        lessons.append("deterministic_loop_completed")
    return lessons
