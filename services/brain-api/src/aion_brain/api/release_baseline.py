"""Release baseline API."""

from functools import lru_cache
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query

from aion_brain.api.scenarios import get_scenario_runner
from aion_brain.config import get_settings
from aion_brain.contracts.release_baseline import (
    ReleaseBaselineReport,
    ReleaseBaselineRequest,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.policy.opa_adapter import OPAAdapter
from aion_brain.release_baseline.repository import ReleaseBaselineRepository
from aion_brain.release_baseline.service import ReleaseBaselineService

router = APIRouter(prefix="/brain/release-baseline", tags=["release-baseline"])


def get_release_baseline_repository() -> ReleaseBaselineRepository:
    """Return the configured release baseline repository."""
    return get_cached_release_baseline_repository(get_settings().database_url)


@lru_cache
def get_cached_release_baseline_repository(database_url: str) -> ReleaseBaselineRepository:
    """Return a cached release baseline repository."""
    return ReleaseBaselineRepository(database_url)


def get_release_baseline_service() -> ReleaseBaselineService:
    """Return the configured release baseline service."""
    settings = get_settings()
    return ReleaseBaselineService(
        get_scenario_runner(),
        get_cached_release_baseline_repository(settings.database_url),
        OPAAdapter(settings.opa_url),
        settings=settings,
    )


@router.post("/run", response_model=ReleaseBaselineReport)
def run_release_baseline(
    request: ReleaseBaselineRequest,
    service: Annotated[ReleaseBaselineService, Depends(get_release_baseline_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
) -> ReleaseBaselineReport:
    """Run a deterministic release baseline."""
    request = request.model_copy(
        update={
            "created_by": request.created_by or actor_context.actor_id,
            "owner_scope": request.owner_scope or actor_context.security_scope,
        }
    )
    return service.run(request)


@router.get("/{release_baseline_id}", response_model=ReleaseBaselineReport)
def get_release_baseline(
    release_baseline_id: str,
    service: Annotated[ReleaseBaselineService, Depends(get_release_baseline_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
) -> ReleaseBaselineReport:
    """Return a release baseline report."""
    report = service.get(release_baseline_id, _scope(scope, actor_context))
    if report is None:
        raise HTTPException(status_code=404, detail="release_baseline_not_found")
    return report


@router.get("", response_model=list[ReleaseBaselineReport])
def list_release_baselines(
    service: Annotated[ReleaseBaselineService, Depends(get_release_baseline_service)],
    actor_context: Annotated[ActorContext, Depends(get_actor_context)],
    scope: Annotated[list[str] | None, Query()] = None,
    version: str | None = None,
    status: str | None = None,
    limit: Annotated[int, Query(ge=1, le=500)] = 50,
) -> list[ReleaseBaselineReport]:
    """List release baseline reports."""
    return service.list(
        scope=_scope(scope, actor_context),
        version=version,
        status=status,
        limit=limit,
    )


def _scope(scope: list[str] | None, actor_context: ActorContext) -> list[str]:
    value = scope or actor_context.security_scope
    if not value:
        raise HTTPException(status_code=422, detail="scope_required")
    return value
