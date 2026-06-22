"""Decision recommendation orchestration service."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.counterfactuals import CounterfactualRunRequest
from aion_brain.contracts.decisions import DecisionEvaluationRequest, DecisionRecommendation
from aion_brain.decisions.counterfactuals import CounterfactualSimulator
from aion_brain.decisions.evaluator import OptionEvaluator
from aion_brain.decisions.options import DecisionOptionService
from aion_brain.decisions.repository import DecisionRepository


class DecisionRecommendationService:
    """Build a recommendation packet without auto-execution."""

    def __init__(
        self,
        repository: DecisionRepository,
        option_service: DecisionOptionService,
        evaluator: OptionEvaluator,
        counterfactuals: CounterfactualSimulator,
        *,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._option_service = option_service
        self._evaluator = evaluator
        self._counterfactuals = counterfactuals
        self._settings = settings

    def recommend(
        self,
        decision_frame_id: str,
        utility_profile_id: str | None = None,
        approval_present: bool = False,
        dry_run: bool = True,
    ) -> DecisionRecommendation:
        frame = self._repository.get_frame(decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        if not self._repository.list_options(decision_frame_id):
            self._option_service.propose_default_options(decision_frame_id)
        recommendation = self._evaluator.evaluate(
            DecisionEvaluationRequest(
                decision_frame_id=decision_frame_id,
                utility_profile_id=utility_profile_id,
                approval_present=approval_present,
                dry_run=dry_run,
                include_counterfactuals=bool(
                    getattr(self._settings, "counterfactuals_enabled", True)
                ),
            )
        )
        counterfactual_runs = []
        if bool(getattr(self._settings, "counterfactuals_enabled", True)):
            for option in recommendation.options:
                counterfactual_runs.append(
                    self._counterfactuals.run(
                        CounterfactualRunRequest(
                            decision_frame_id=decision_frame_id,
                            decision_option_id=option.decision_option_id,
                            trace_id=frame.trace_id,
                            mode="dry_run",
                            owner_scope=frame.owner_scope,
                            input_state={"decision_frame_id": decision_frame_id},
                            assumptions=frame.assumptions,
                        )
                    )
                )
        return recommendation.model_copy(
            update={
                "counterfactuals": counterfactual_runs,
                "created_at": datetime.now(recommendation.created_at.tzinfo),
            }
        )
