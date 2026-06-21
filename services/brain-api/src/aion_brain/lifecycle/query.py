"""Scope-gated lifecycle query facade."""

from __future__ import annotations


class LifecycleQueryService:
    """Query lifecycle-owned records through repository methods."""

    def __init__(self, repository: object) -> None:
        self._repository = repository

    def status(self, scope: list[str]) -> dict[str, object]:
        reports = _call(self._repository, "list_reports", scope, limit=1)
        return {
            "status": "healthy" if reports else "warning",
            "latest_report_available": bool(reports),
        }


def _call(repository: object, method_name: str, scope: list[str], **kwargs: object) -> list[object]:
    method = getattr(repository, method_name, None)
    return list(method(scope, **kwargs) or []) if callable(method) else []


__all__ = ["LifecycleQueryService"]
