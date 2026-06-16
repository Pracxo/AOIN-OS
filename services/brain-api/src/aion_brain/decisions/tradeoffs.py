"""Tradeoff matrix service."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.decisions import (
    REQUIRED_UTILITY_WEIGHTS,
    DecisionFrame,
    DecisionOption,
    OptionEvaluation,
    TradeoffMatrix,
    UtilityProfile,
)
from aion_brain.decisions._shared import LOW_TO_HIGH_RISK, emit_telemetry
from aion_brain.decisions.repository import DecisionRepository


class TradeoffMatrixService:
    """Build deterministic tradeoff matrices."""

    def __init__(
        self,
        repository: DecisionRepository,
        *,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._telemetry_service = telemetry_service

    def build_matrix(
        self,
        frame: DecisionFrame,
        options: list[DecisionOption],
        evaluations: list[OptionEvaluation],
        profile: UtilityProfile,
    ) -> TradeoffMatrix:
        by_option = {item.decision_option_id: item for item in options}
        scores = {
            evaluation.decision_option_id: {
                key: float(evaluation.factors.get(key, 0.0)) for key in REQUIRED_UTILITY_WEIGHTS
            }
            for evaluation in evaluations
        }
        ranked = sorted(
            (
                evaluation
                for evaluation in evaluations
                if evaluation.status != "blocked" and evaluation.decision_option_id in by_option
            ),
            key=lambda item: (
                -item.score,
                LOW_TO_HIGH_RISK.get(by_option[item.decision_option_id].risk_level, 9),
                _reversibility_rank(by_option[item.decision_option_id].reversibility),
                item.decision_option_id,
            ),
        )
        matrix = TradeoffMatrix(
            tradeoff_matrix_id=f"tradeoff-matrix-{uuid4().hex}",
            decision_frame_id=frame.decision_frame_id,
            utility_profile_id=profile.utility_profile_id,
            option_ids=[item.decision_option_id for item in options],
            criteria=list(REQUIRED_UTILITY_WEIGHTS),
            scores=scores,
            recommended_option_id=ranked[0].decision_option_id if ranked else None,
            metadata={"deterministic": True},
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_tradeoff_matrix(matrix)
        emit_telemetry(
            self._telemetry_service,
            event_type="tradeoff_matrix_created",
            node_type="tradeoff",
            node_id=stored.tradeoff_matrix_id,
            intensity=0.6,
            trace_id=frame.trace_id,
            payload={"owner_scope": frame.owner_scope, "recommended": stored.recommended_option_id},
        )
        return stored


def _reversibility_rank(value: str) -> int:
    return {
        "reversible": 0,
        "partially_reversible": 1,
        "unknown": 2,
        "irreversible": 3,
    }.get(value, 4)
