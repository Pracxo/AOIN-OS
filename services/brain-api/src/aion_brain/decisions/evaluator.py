"""Deterministic option evaluator."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.decisions import (
    DecisionEvaluationRequest,
    DecisionFrame,
    DecisionOption,
    DecisionRecommendation,
    OptionEvaluation,
    UtilityProfile,
)
from aion_brain.decisions._shared import authorize, call_optional, emit_telemetry
from aion_brain.decisions.repository import DecisionRepository
from aion_brain.decisions.tradeoffs import TradeoffMatrixService
from aion_brain.decisions.utility import UtilityProfileService


class OptionEvaluator:
    """Score options with deterministic generic factors."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        utility_profiles: UtilityProfileService,
        tradeoffs: TradeoffMatrixService,
        *,
        risk_engine: object | None = None,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._utility_profiles = utility_profiles
        self._tradeoffs = tradeoffs
        self._risk_engine = risk_engine
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service
        self._settings = settings

    def evaluate(self, request: DecisionEvaluationRequest) -> DecisionRecommendation:
        frame = self._repository.get_frame(request.decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        authorize(
            self._policy_adapter,
            action_type="decision.evaluate",
            resource_type="decision_frame",
            resource_id=frame.decision_frame_id,
            scope=frame.owner_scope,
            trace_id=frame.trace_id,
            actor_id=frame.actor_id,
            workspace_id=frame.workspace_id,
            risk_level="medium",
            approval_present=request.approval_present,
            context={"dry_run": request.dry_run},
        )
        profile = (
            self._utility_profiles.get_profile(request.utility_profile_id, frame.owner_scope)
            if request.utility_profile_id
            else None
        ) or self._utility_profiles.default_profile(frame.owner_scope)
        options = self._repository.list_options(frame.decision_frame_id)
        if request.option_ids:
            requested = set(request.option_ids)
            options = [item for item in options if item.decision_option_id in requested]
        if not options:
            options = []
        evaluations = [
            self.evaluate_option(frame, option, profile, request.approval_present)
            for option in options
        ]
        evaluations = _rank(evaluations)
        for item in evaluations:
            self._repository.save_evaluation(item)
        matrix = self._tradeoffs.build_matrix(frame, options, evaluations, profile)
        recommendation = DecisionRecommendation(
            decision_frame=frame.model_copy(
                update={"status": "evaluated", "updated_at": datetime.now(UTC)}
            ),
            options=options,
            evaluations=evaluations,
            tradeoff_matrix=matrix,
            counterfactuals=[],
            recommended_option_id=matrix.recommended_option_id,
            constraints=_unique(
                [constraint for item in evaluations for constraint in item.constraints]
            ),
            explanation=_recommendation_explanation(matrix.recommended_option_id, options),
            created_at=datetime.now(UTC),
        )
        self._repository.save_frame(recommendation.decision_frame)
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_recommendation_created",
            node_type="decision",
            node_id=frame.decision_frame_id,
            intensity=0.8,
            trace_id=frame.trace_id,
            payload={
                "owner_scope": frame.owner_scope,
                "recommended_option_id": recommendation.recommended_option_id,
            },
        )
        return recommendation

    def evaluate_option(
        self,
        frame: DecisionFrame,
        option: DecisionOption,
        profile: UtilityProfile,
        approval_present: bool,
    ) -> OptionEvaluation:
        factors = {
            "goal_alignment": _goal_alignment(frame, option),
            "evidence_support": _evidence_support(frame, option),
            "belief_confidence": _belief_confidence(frame),
            "risk_reduction": _risk_reduction(option.risk_level),
            "policy_allowance": _policy_allowance(self._policy_adapter, frame, option),
            "autonomy_allowance": _autonomy_allowance(self._autonomy_governor, frame, option),
            "reversibility": _reversibility(option.reversibility),
            "cost_efficiency": _cost_efficiency(option.cost_estimate),
            "urgency": _urgency(option.metadata),
            "uncertainty_reduction": _uncertainty_reduction(frame, option),
        }
        constraints: list[str] = []
        status = "passed"
        if factors["policy_allowance"] == 0.0:
            constraints.append("policy_denied")
            status = "blocked"
        if factors["autonomy_allowance"] == 0.0:
            constraints.append("autonomy_denied")
            status = "blocked"
        if option.risk_level in {"high", "critical"} and not approval_present:
            constraints.append("approval_required")
            if status != "blocked":
                status = "warning"
        if option.option_type == "controlled_action" and not bool(
            getattr(self._settings, "decision_controlled_mode_enabled", False)
        ):
            constraints.append("controlled_option_not_recommended")
            status = "blocked"
        risk_result = call_optional(
            self._risk_engine,
            ("assess_option", "assess", "evaluate"),
            option,
        )
        risk_id = str(getattr(risk_result, "risk_assessment_id", "")) or None
        weighted_score = sum(float(profile.weights[key]) * factors[key] for key in profile.weights)
        score = max(0.0, min(1.0, weighted_score))
        evaluation = OptionEvaluation(
            option_evaluation_id=f"option-eval-{uuid4().hex}",
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id,
            utility_profile_id=profile.utility_profile_id,
            status=status,  # type: ignore[arg-type]
            score=score,
            rank=None,
            factors=factors,
            policy_decision_id=None,
            autonomy_decision_id=None,
            risk_assessment_id=risk_id,
            approval_request_id=None,
            tradeoffs={"weights": profile.weights},
            constraints=constraints,
            explanation=f"Deterministic score {score:.2f} from generic utility factors.",
            metadata={"no_execution": True},
            created_at=datetime.now(UTC),
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="decision_option_evaluated",
            node_type="option_evaluation",
            node_id=evaluation.option_evaluation_id,
            intensity=evaluation.score,
            trace_id=frame.trace_id,
            edge_from=option.decision_option_id,
            edge_to=evaluation.option_evaluation_id,
            payload={"owner_scope": frame.owner_scope, "status": evaluation.status},
        )
        return evaluation


def _goal_alignment(frame: DecisionFrame, option: DecisionOption) -> float:
    if option.target_id and option.target_id in {*frame.goal_refs, *frame.task_refs}:
        return 1.0
    if not frame.goal_refs and not frame.task_refs:
        return 0.5
    return 0.6 if option.option_type in {"create_plan", "revise_plan"} else 0.3


def _evidence_support(frame: DecisionFrame, option: DecisionOption) -> float:
    refs = option.metadata.get("evidence_refs")
    if isinstance(refs, list) and refs:
        return 1.0
    if frame.evidence_refs:
        return 1.0
    if frame.memory_refs:
        return 0.5
    return 0.2


def _belief_confidence(frame: DecisionFrame) -> float:
    raw = frame.metadata.get("belief_confidences")
    if isinstance(raw, list) and raw:
        values = [float(item) for item in raw if isinstance(item, int | float)]
        if values:
            return max(0.0, min(1.0, sum(values) / len(values)))
    if "contradicted_belief" in frame.constraints:
        return 0.2
    if "stale_belief" in frame.constraints:
        return 0.35
    return 0.5


def _risk_reduction(risk_level: str) -> float:
    return {"low": 1.0, "medium": 0.7, "high": 0.3, "critical": 0.1}.get(risk_level, 0.2)


def _policy_allowance(
    policy_adapter: object,
    frame: DecisionFrame,
    option: DecisionOption,
) -> float:
    if not option.action_type:
        return 0.5
    try:
        authorize(
            policy_adapter,
            action_type=option.action_type,
            resource_type=option.target_type or "decision_option",
            resource_id=option.target_id or option.decision_option_id,
            scope=frame.owner_scope,
            trace_id=frame.trace_id,
            actor_id=frame.actor_id,
            workspace_id=frame.workspace_id,
            risk_level=option.risk_level,
            context={"decision_frame_id": frame.decision_frame_id},
        )
    except PermissionError:
        return 0.0
    except Exception:
        return 0.5
    return 1.0


def _autonomy_allowance(
    autonomy_governor: object | None,
    frame: DecisionFrame,
    option: DecisionOption,
) -> float:
    if not option.action_type:
        return 0.5
    if autonomy_governor is None:
        return 0.5
    result = call_optional(
        autonomy_governor,
        ("authorize", "authorize_action", "decide"),
        action_type=option.action_type,
        risk_level=option.risk_level,
        scope=frame.owner_scope,
    )
    if result is None:
        return 0.5
    if getattr(result, "allow", None) is False or getattr(result, "allowed", None) is False:
        return 0.0
    return 1.0


def _reversibility(value: str) -> float:
    return {
        "reversible": 1.0,
        "partially_reversible": 0.6,
        "unknown": 0.4,
        "irreversible": 0.1,
    }.get(value, 0.4)


def _cost_efficiency(cost_estimate: dict[str, Any]) -> float:
    raw = cost_estimate.get("relative_cost") or cost_estimate.get("cost")
    if isinstance(raw, int | float):
        return max(0.0, min(1.0, 1.0 - float(raw)))
    return 0.5


def _urgency(metadata: dict[str, Any]) -> float:
    raw = metadata.get("urgency")
    if isinstance(raw, int | float):
        return max(0.0, min(1.0, float(raw)))
    return 0.5


def _uncertainty_reduction(frame: DecisionFrame, option: DecisionOption) -> float:
    if any(item in frame.constraints for item in ("unclear_goal", "high_uncertainty")):
        if option.option_type in {"clarify", "retrieve_more_context"}:
            return 1.0
    return 0.5


def _rank(evaluations: list[OptionEvaluation]) -> list[OptionEvaluation]:
    ranked = sorted(
        evaluations,
        key=lambda item: (
            item.status == "blocked",
            -item.score,
            item.decision_option_id,
        ),
    )
    return [item.model_copy(update={"rank": index + 1}) for index, item in enumerate(ranked)]


def _recommendation_explanation(option_id: str | None, options: list[DecisionOption]) -> str:
    if option_id is None:
        return "No available option passed the deterministic decision checks."
    option = next((item for item in options if item.decision_option_id == option_id), None)
    title = option.title if option else option_id
    return f"The strongest available option is {title}. This is a recommendation, not execution."


def _unique(values: list[str]) -> list[str]:
    return list(dict.fromkeys(value for value in values if value))
