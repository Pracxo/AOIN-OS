"""Local deterministic regression and evaluation adapter API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, ConfigDict

from aion_brain.api.replay import get_replay_service, get_snapshot_service
from aion_brain.config import get_settings
from aion_brain.contracts.regression import (
    EvalAdapterRunRequest,
    EvalAdapterRunResult,
    RegressionCase,
    RegressionCaseCreateRequest,
    RegressionRun,
    RegressionRunRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.evaluation.adapters.base import EvaluationAdapter
from aion_brain.evaluation.adapters.local_adapter import LocalEvaluationAdapter
from aion_brain.evaluation.adapters.promptfoo_adapter import PromptfooAdapter
from aion_brain.evaluation.adapters.ragas_adapter import RagasAdapter
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.regression.report import RegressionReportBuilder
from aion_brain.regression.repository import RegressionRepository
from aion_brain.regression.service import RegressionService
from aion_brain.replay.service import ReplayService
from aion_brain.replay.snapshot import ReplayPolicyDenied, SnapshotService

router = APIRouter(prefix="/brain", tags=["regression"])


class DisableCaseRequest(BaseModel):
    """Request to disable a regression case."""

    model_config = ConfigDict(extra="forbid")

    reason: str


@lru_cache
def get_cached_regression_repository(database_url: str) -> RegressionRepository:
    """Return the cached regression repository."""
    return RegressionRepository(database_url)


def get_regression_service(
    replay_service: Annotated[ReplayService, Depends(get_replay_service)],
    snapshot_service: Annotated[SnapshotService, Depends(get_snapshot_service)],
) -> RegressionService:
    """Return the configured local regression service."""
    settings = get_settings()
    return RegressionService(
        get_cached_regression_repository(settings.database_url),
        replay_service,
        snapshot_service,
        OPAAdapter(settings.opa_url),
        telemetry_service=None,
        report_builder=RegressionReportBuilder(),
    )


@router.post("/regression/cases", response_model=RegressionCase)
def create_regression_case(
    request: RegressionCaseCreateRequest,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegressionCase:
    """Create a golden trace regression case."""
    try:
        return service.with_actor_context(actor_context).create_case(
            request.model_copy(update={"created_by": request.created_by or actor_context.actor_id})
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.get("/regression/cases/{case_id}", response_model=RegressionCase)
def get_regression_case(
    case_id: str,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RegressionCase:
    """Return a golden trace regression case."""
    try:
        case = service.with_actor_context(actor_context).get_case(
            case_id, _scope(scope, actor_context)
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if case is None:
        raise HTTPException(status_code=404, detail="regression_case_not_found")
    return case


@router.get("/regression/cases", response_model=list[RegressionCase])
def list_regression_cases(
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    status: str | None = None,
    tags: Annotated[list[str] | None, Query()] = None,
    limit: Annotated[int, Query(ge=1, le=1000)] = 50,
) -> list[RegressionCase]:
    """List golden trace regression cases."""
    try:
        return service.with_actor_context(actor_context).list_cases(
            _scope(scope, actor_context), status, tags, limit
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc


@router.post("/regression/cases/{case_id}/disable", response_model=RegressionCase)
def disable_regression_case(
    case_id: str,
    request: DisableCaseRequest,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegressionCase:
    """Disable a golden trace regression case."""
    try:
        return service.with_actor_context(actor_context).disable_case(case_id, request.reason)
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.post("/regression/run", response_model=RegressionRun)
def run_regression(
    request: RegressionRunRequest,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> RegressionRun:
    """Run selected local deterministic regression cases."""
    enriched = request.model_copy(
        update={"created_by": request.created_by or actor_context.actor_id}
    )
    return service.with_actor_context(actor_context).run_regression(enriched)


@router.get("/regression/runs/{regression_run_id}", response_model=RegressionRun)
def get_regression_run(
    regression_run_id: str,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> RegressionRun:
    """Return a local deterministic regression run."""
    try:
        run = service.with_actor_context(actor_context).get_run(
            regression_run_id, _scope(scope, actor_context)
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    if run is None:
        raise HTTPException(status_code=404, detail="regression_run_not_found")
    return run


@router.post("/eval/adapters/run", response_model=EvalAdapterRunResult)
def run_eval_adapter(
    request: EvalAdapterRunRequest,
    service: Annotated[RegressionService, Depends(get_regression_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> EvalAdapterRunResult:
    """Run an evaluation adapter behind the AION boundary."""
    adapters: dict[str, EvaluationAdapter] = {
        "local": LocalEvaluationAdapter(),
        "promptfoo": PromptfooAdapter(),
        "ragas": RagasAdapter(),
    }
    try:
        return service.with_actor_context(actor_context).run_eval_adapter(
            request, adapters[request.adapter_name]
        )
    except ReplayPolicyDenied as exc:
        raise _policy_denied(exc) from exc
    except NotImplementedError as exc:
        raise HTTPException(status_code=501, detail=str(exc)) from exc


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value


def _policy_denied(exc: ReplayPolicyDenied) -> HTTPException:
    return HTTPException(
        status_code=403,
        detail={"reason": exc.decision.reason, "constraints": exc.decision.constraints},
    )
