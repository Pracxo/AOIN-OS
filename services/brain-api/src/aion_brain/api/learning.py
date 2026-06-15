"""Learning API."""

from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from aion_brain.api.dependencies import get_audit_repository, get_learning_engine
from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.learning import LearningSignal
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.learning.engine import LearningEngine

router = APIRouter(prefix="/brain", tags=["learning"])


class LearnRequest(BaseModel):
    """Learning signal request."""

    model_config = ConfigDict(extra="forbid")

    trace: DecisionTrace
    evaluation: EvaluationRecord


@router.get("/traces/{trace_id}/learning", response_model=list[LearningSignal])
def list_trace_learning(
    trace_id: str,
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> list[LearningSignal]:
    """Return persisted learning signals for a trace."""
    return repository.list_learning_signals(trace_id)


@router.post("/learn", response_model=LearningSignal)
def learn_from_trace(
    request: LearnRequest,
    learning_engine: Annotated[LearningEngine, Depends(get_learning_engine)],
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> LearningSignal:
    """Create and persist a candidate learning signal."""
    signal = learning_engine.create_signal(trace=request.trace, evaluation=request.evaluation)
    repository.save_learning_signal(signal)
    return signal
