"""Operator status card aggregation."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.operator import (
    OperatorCardStatus,
    OperatorCategory,
    OperatorSeverity,
    OperatorStatusCard,
)

_CARD_SPECS: tuple[tuple[str, str, OperatorCategory, str], ...] = (
    ("kernel", "Kernel Status", "kernel", "kernel_service"),
    ("health", "Health Readiness", "health", "health_service"),
    ("resilience", "Resilience Status", "resilience", "resilience_service"),
    ("security", "Security Hardening", "security", "security_service"),
    ("runtime_config", "Runtime Configuration", "runtime_config", "runtime_config_service"),
    ("audit", "Audit Integrity", "audit", "audit_service"),
    ("policy", "Policy Coverage", "policy", "policy_service"),
    ("freeze", "Freeze Gate", "release", "freeze_service"),
    ("release", "Release Baseline", "release", "release_service"),
    ("performance", "Performance Baseline", "performance", "performance_service"),
    ("backups", "Backup Status", "backups", "backup_service"),
    ("outbox", "Outbox Pending", "events", "outbox_service"),
    ("approvals", "Approval Pending", "approvals", "approval_service"),
    ("workflows", "Workflow Failures", "workflows", "workflow_service"),
    ("event_dead_letters", "Event Dead Letters", "events", "event_router_service"),
    ("situations", "Active Situations", "memory", "situation_service"),
    ("decisions", "Open Decisions", "approvals", "decision_frame_service"),
    ("outcomes", "Outcome Ledger", "audit", "outcome_service"),
    ("learning", "Learning Synthesis", "learning", "learning_synthesizer"),
    ("self_model", "Self Model", "self_model", "self_model_service"),
    ("capability_awareness", "Capability Awareness", "self_model", "capability_awareness_service"),
    ("limitations", "Limitation Ledger", "self_model", "limitation_service"),
    ("instructions", "Instruction Hierarchy", "operator", "instruction_service"),
    ("prompts", "Prompt Governance", "operator", "prompt_service"),
    ("scheduler", "Temporal Scheduler", "scheduler", "scheduler_service"),
    ("incidents", "Open Incidents", "incidents", "incident_service"),
    ("registry", "Resource Registry", "registry", "registry_service"),
    ("contract_registry", "Contract Registry", "registry", "contract_registry_service"),
    ("extension_registry", "Extension Registry", "registry", "extension_registry_service"),
    ("lifecycle", "Data Lifecycle", "lifecycle", "lifecycle_service"),
)


class StatusCardBuilder:
    """Build read-only status cards from local subsystem contracts."""

    def __init__(self, **services: object) -> None:
        self._services = services

    def build_cards(self, scope: list[str]) -> list[OperatorStatusCard]:
        """Build operator status cards, degrading gracefully for missing services."""
        return [
            self._build_card(key, title, category, service_key, scope)
            for key, title, category, service_key in _CARD_SPECS
        ]

    def _build_card(
        self,
        key: str,
        title: str,
        category: OperatorCategory,
        service_key: str,
        scope: list[str],
    ) -> OperatorStatusCard:
        service = self._services.get(service_key)
        if service is None:
            return _card(
                key,
                title,
                category,
                "warning",
                "medium",
                "Optional local service is unavailable.",
                source_type=service_key,
                metadata={"available": False, "scope": scope},
            )
        try:
            raw = _read_status(service, scope)
        except Exception as exc:
            return _card(
                key,
                title,
                category,
                "warning",
                "medium",
                "Local service status could not be read.",
                source_type=service_key,
                metadata={"available": True, "error": exc.__class__.__name__},
            )
        status = _normalize_status(raw)
        severity = _severity_for_status(status)
        return _card(
            key,
            title,
            category,
            status,
            severity,
            _summary_for_status(title, status),
            source_type=service_key,
            metric=_metric_for(raw),
            metadata={"available": True},
        )


def _card(
    key: str,
    title: str,
    category: OperatorCategory,
    status: OperatorCardStatus,
    severity: OperatorSeverity,
    summary: str,
    *,
    source_type: str,
    metric: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> OperatorStatusCard:
    return OperatorStatusCard(
        card_id=f"card-{key}",
        title=title,
        category=category,
        status=status,
        severity=severity,
        summary=summary,
        metric=metric or {},
        source_type=source_type,
        source_id=None,
        updated_at=datetime.now(UTC),
        metadata=metadata or {},
    )


def _read_status(service: object, scope: list[str]) -> object:
    for name in ("status", "readiness", "latest_status"):
        method = getattr(service, name, None)
        if callable(method):
            return _call(method, scope)
    run = getattr(service, "run", None)
    if callable(run):
        return _call(run, scope)
    list_method = getattr(service, "list", None)
    if callable(list_method):
        return _call(list_method, scope)
    return service


def _call(method: object, scope: list[str]) -> object:
    callable_method = cast(Any, method)
    for kwargs in ({"scope": scope}, {}):
        try:
            return cast(object, callable_method(**kwargs))
        except TypeError:
            continue
    try:
        return cast(object, callable_method(scope))
    except TypeError:
        return cast(object, callable_method())


def _normalize_status(raw: object) -> OperatorCardStatus:
    if isinstance(raw, list):
        statuses = [_normalize_status(item) for item in raw]
        if any(status == "failed" for status in statuses):
            return "failed"
        if any(status in {"blocked", "degraded"} for status in statuses):
            return "degraded"
        if any(status == "warning" for status in statuses):
            return "warning"
        return "healthy" if statuses else "unknown"
    if isinstance(raw, dict):
        candidate = raw.get("status") or raw.get("overall_status") or raw.get("verification_status")
    else:
        candidate = getattr(raw, "status", None) or getattr(raw, "overall_status", None)
    text = str(candidate or "healthy").lower()
    if text in {"ok", "alive", "healthy"}:
        return "healthy"
    if text in {"ready"}:
        return "ready"
    if text in {"passed", "pass"}:
        return "passed"
    if text in {"warning", "not_run", "unavailable"}:
        return "warning"
    if text in {"degraded"}:
        return "degraded"
    if text in {"blocked", "blocked_by_policy"}:
        return "blocked"
    if text in {"failed", "fail", "critical", "open"}:
        return "failed"
    return "unknown"


def _severity_for_status(status: OperatorCardStatus) -> OperatorSeverity:
    if status == "failed":
        return "critical"
    if status in {"blocked", "degraded"}:
        return "high"
    if status in {"warning", "unknown"}:
        return "medium"
    return "low"


def _summary_for_status(title: str, status: OperatorCardStatus) -> str:
    if status in {"healthy", "ready", "passed"}:
        return f"{title} is locally available."
    if status == "warning":
        return f"{title} needs operator review."
    if status == "degraded":
        return f"{title} is degraded."
    if status == "blocked":
        return f"{title} is blocked."
    if status == "failed":
        return f"{title} has a failure signal."
    return f"{title} status is unknown."


def _metric_for(raw: object) -> dict[str, Any]:
    if isinstance(raw, list):
        return {"item_count": len(raw)}
    if isinstance(raw, dict):
        return {
            key: value for key, value in raw.items() if isinstance(value, (int, float, bool, str))
        }
    metric: dict[str, Any] = {}
    for key in ("pending_count", "failed_count", "latest_sequence", "checked_count"):
        value = getattr(raw, key, None)
        if isinstance(value, (int, float, bool, str)):
            metric[key] = value
    if not metric:
        metric["status_read_id"] = uuid4().hex
    return metric
