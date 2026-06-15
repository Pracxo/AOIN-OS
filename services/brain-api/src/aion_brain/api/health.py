"""Health endpoint for the Brain API."""

from collections.abc import Callable
from typing import Annotated, Literal

from fastapi import APIRouter, Depends

from aion_brain.config import Settings, get_settings
from aion_brain.infra import check_nats, check_opa, check_postgres, check_redis
from aion_brain.logging import log_event

CheckState = Literal["ok", "fail"]

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    """Return service health metadata."""
    return {
        "status": "ok",
        "service": "aion-brain-api",
        "version": "0.1.0",
    }


@router.get("/health/live")
def live(settings: Annotated[Settings, Depends(get_settings)]) -> dict[str, str]:
    """Return process liveness metadata."""
    return {
        "status": "alive",
        "service": settings.service_name,
        "version": settings.version,
    }


@router.get("/health/ready")
def ready(
    settings: Annotated[Settings, Depends(get_settings)],
) -> dict[str, str | dict[str, CheckState]]:
    """Return dependency readiness without crashing on failures."""
    checks = run_readiness_checks(settings)
    status = "ready" if all(result == "ok" for result in checks.values()) else "degraded"
    log_event(
        "readiness checked",
        settings=settings,
        fields={"status": status, "checks": checks},
    )
    return {"status": status, "checks": checks}


def run_readiness_checks(settings: Settings) -> dict[str, CheckState]:
    """Run all readiness checks behind infrastructure boundaries."""
    return {
        "postgres": _check(lambda: check_postgres(settings.database_url)),
        "redis": _check(lambda: check_redis(settings.redis_url)),
        "nats": _check(lambda: check_nats(settings.nats_url)),
        "opa": _check(lambda: check_opa(settings.opa_url)),
    }


def _check(checker: Callable[[], bool]) -> CheckState:
    """Convert any checker failure into a stable readiness state."""
    try:
        return "ok" if checker() else "fail"
    except Exception:
        return "fail"
