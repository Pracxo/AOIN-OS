"""Run supervision query facade."""

from __future__ import annotations

from aion_brain.contracts.run_supervision import RunSupervisionRecord
from aion_brain.contracts.scopes import ActorContext


class RunSupervisionQueryService:
    """Read run supervision state through the main supervision service."""

    def __init__(
        self,
        run_supervision_service: object,
        *,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._run_supervision_service = run_supervision_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> RunSupervisionQueryService:
        service = getattr(self._run_supervision_service, "with_actor_context", None)
        scoped = service(actor_context) if callable(service) else self._run_supervision_service
        return RunSupervisionQueryService(scoped, actor_context=actor_context)

    def query(
        self,
        scope: list[str],
        target_system: str | None = None,
        status: str | None = None,
        stalled: bool | None = None,
        limit: int = 100,
    ) -> list[RunSupervisionRecord]:
        query = getattr(self._run_supervision_service, "query", None)
        if not callable(query):
            return []
        result = query(
            scope=scope,
            target_system=target_system,
            status=status,
            stalled=stalled,
            limit=limit,
        )
        return [item for item in result if isinstance(item, RunSupervisionRecord)]


__all__ = ["RunSupervisionQueryService"]
