"""Trace and evaluation API."""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from aion_brain.api.dependencies import get_audit_repository, get_evaluator
from aion_brain.audit.repository import AuditRepository
from aion_brain.contracts.evaluation import EvaluationRecord
from aion_brain.contracts.traces import DecisionTrace
from aion_brain.evaluation.evaluator import Evaluator

router = APIRouter(prefix="/brain", tags=["traces"])


@router.get("/traces/{trace_id}", response_model=DecisionTrace)
def get_trace(
    trace_id: str,
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> DecisionTrace:
    """Return a persisted decision trace."""
    trace = repository.get_trace(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace_not_found")
    return trace


@router.get("/traces/{trace_id}/evaluation", response_model=EvaluationRecord)
def get_trace_evaluation(
    trace_id: str,
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> EvaluationRecord:
    """Return a persisted trace evaluation."""
    evaluation = repository.get_evaluation(trace_id)
    if evaluation is None:
        raise HTTPException(status_code=404, detail="evaluation_not_found")
    return evaluation


@router.post("/evaluate", response_model=EvaluationRecord)
def evaluate_trace(
    trace: DecisionTrace,
    evaluator: Annotated[Evaluator, Depends(get_evaluator)],
    repository: Annotated[AuditRepository, Depends(get_audit_repository)],
) -> EvaluationRecord:
    """Evaluate and persist a decision trace evaluation."""
    evaluation = evaluator.evaluate(trace)
    repository.save_evaluation(evaluation)
    return evaluation
