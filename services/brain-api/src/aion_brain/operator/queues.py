"""Operator queue summary aggregation."""

from __future__ import annotations

from datetime import datetime
from typing import Any, cast

from aion_brain.contracts.operator import (
    OperatorCardStatus,
    OperatorQueueSummary,
    OperatorQueueType,
    OperatorSeverity,
)

_QUEUE_SPECS: tuple[tuple[OperatorQueueType, str, str, tuple[str, ...]], ...] = (
    ("approvals", "Approvals", "approval_service", ("list_requests", "list")),
    ("commands", "Commands", "command_service", ("list_commands", "list")),
    ("outbox", "Outbox", "outbox_service", ("list_messages", "list")),
    ("inbox", "Inbox", "inbox_service", ("list_messages", "list")),
    ("workflows", "Workflows", "workflow_service", ("list_runs", "list_workflows", "list")),
    ("tasks", "Tasks", "task_service", ("list_tasks", "list")),
    ("dead_letters", "Event Dead Letters", "event_router_service", ("list_dead_letters", "list")),
    ("backups", "Backup Jobs", "backup_service", ("list_jobs", "list_backups", "list")),
    ("release_packages", "Release Packages", "release_service", ("list_packages", "list")),
    (
        "audit_verifications",
        "Audit Verifications",
        "audit_service",
        ("list_verification_runs", "list"),
    ),
    ("resilience_tests", "Resilience Tests", "resilience_service", ("list_test_runs", "list")),
    ("security_scans", "Security Scans", "security_service", ("list_scans", "list")),
    ("scenarios", "Scenarios", "scenario_service", ("list_runs", "list_scenarios", "list")),
    (
        "drift_findings",
        "Interface Drift Findings",
        "contract_registry_repository",
        ("list_findings",),
    ),
    (
        "migration_notes",
        "Migration Notes",
        "contract_registry_repository",
        ("list_migration_notes",),
    ),
    ("compatibility_scans", "Compatibility Scans", "contract_registry_repository", ("list_scans",)),
    (
        "extension_packages",
        "Extension Packages",
        "extension_registry_repository",
        ("list_packages",),
    ),
    (
        "extension_reviews",
        "Extension Reviews",
        "extension_registry_repository",
        ("list_reviews",),
    ),
    (
        "extension_compatibility",
        "Extension Compatibility",
        "extension_registry_repository",
        ("list_compatibility_runs",),
    ),
    (
        "extension_install_plans",
        "Extension Install Plans",
        "extension_registry_repository",
        ("list_install_plans",),
    ),
    ("module_slots", "Module Slots", "module_binding_repository", ("list_slots",)),
    (
        "capability_bindings",
        "Capability Bindings",
        "module_binding_repository",
        ("list_bindings",),
    ),
    (
        "binding_validations",
        "Binding Validations",
        "module_binding_repository",
        ("list_validation_runs",),
    ),
    (
        "binding_conflicts",
        "Binding Conflicts",
        "module_binding_repository",
        ("list_conflicts",),
    ),
    (
        "module_mount_plans",
        "Module Mount Plans",
        "module_binding_repository",
        ("list_mount_plans",),
    ),
    (
        "route_binding_previews",
        "Route Binding Previews",
        "module_binding_repository",
        ("list_route_previews",),
    ),
    (
        "conformance_findings",
        "Conformance Findings",
        "conformance_repository",
        ("list_findings",),
    ),
    (
        "generic",
        "Module Mock Runtime",
        "module_mock_repository",
        ("list_runs", "list_findings", "list_profiles"),
    ),
    (
        "generic",
        "Model Provider Hardening",
        "model_provider_hardening_repository",
        ("list_blockers", "list_readiness", "list_simulations", "list_profiles"),
    ),
    (
        "readiness_assessments",
        "Readiness Assessments",
        "conformance_repository",
        ("list_readiness",),
    ),
    (
        "golden_path_runs",
        "Golden Path Runs",
        "golden_path_repository",
        ("list_runs",),
    ),
    (
        "golden_path_reports",
        "Golden Path Reports",
        "golden_path_repository",
        ("list_reports",),
    ),
    (
        "bootstrap_runs",
        "Bootstrap Runs",
        "bootstrap_repository",
        ("list_runs",),
    ),
    (
        "setup_findings",
        "Setup Findings",
        "bootstrap_repository",
        ("list_findings",),
    ),
    (
        "rc_gate_runs",
        "RC Gate Runs",
        "release_candidate_repository",
        ("list_runs",),
    ),
    (
        "rc_findings",
        "RC Findings",
        "release_candidate_repository",
        ("list_findings",),
    ),
    (
        "rc_reports",
        "RC Reports",
        "release_candidate_repository",
        ("list_reports",),
    ),
    ("generic", "Dialogue Clarifications", "dialogue_service", ("list_pending",)),
    (
        "generic",
        "Belief Contradictions",
        "belief_contradiction_service",
        ("list_contradictions",),
    ),
    (
        "generic",
        "Unresolved Entity Mentions",
        "entity_repository",
        ("list_mentions",),
    ),
    (
        "generic",
        "Entity Merge Proposals",
        "entity_merge_service",
        ("list_proposals",),
    ),
    (
        "generic",
        "Entity Split Proposals",
        "entity_split_service",
        ("list_proposals",),
    ),
    (
        "generic",
        "Situation Projection Runs",
        "situation_projector",
        ("list_failed_runs",),
    ),
    (
        "generic",
        "Open Decision Frames",
        "decision_frame_service",
        ("list_frames",),
    ),
    (
        "generic",
        "Decision Journal",
        "decision_journal_service",
        ("list_records",),
    ),
    (
        "generic",
        "Open Outcome Feedback",
        "outcome_feedback_service",
        ("list_feedback",),
    ),
    (
        "generic",
        "Effect Verification Runs",
        "effect_verifier",
        ("list_verification_runs",),
    ),
    (
        "learning_patterns",
        "Learning Patterns",
        "learning_synthesis_repository",
        ("list_patterns",),
    ),
    (
        "skill_suggestions",
        "Skill Suggestions",
        "skill_suggestion_service",
        ("list_suggestions",),
    ),
    (
        "regression_suggestions",
        "Regression Suggestions",
        "regression_suggestion_service",
        ("list_suggestions",),
    ),
    (
        "generic",
        "Instruction Conflicts",
        "instruction_conflict_service",
        ("list_conflicts",),
    ),
    (
        "generic",
        "Preference Candidates",
        "preference_learning_service",
        ("list_candidates",),
    ),
    (
        "generic",
        "Unsupported Statements",
        "grounding_repository",
        ("list_unsupported",),
    ),
    (
        "generic",
        "Grounding Verifications",
        "grounding_verifier",
        ("list_verification_runs",),
    ),
    (
        "generic",
        "Prompt Injection Findings",
        "prompt_repository",
        ("list_injection_findings",),
    ),
    (
        "generic",
        "Blocked Model Outputs",
        "model_output_repository",
        ("list_outputs",),
    ),
    (
        "generic",
        "Response Candidates",
        "response_candidate_service",
        ("list_candidates",),
    ),
    (
        "generic",
        "Tool Intents",
        "tool_intent_service",
        ("list_tool_intents",),
    ),
    (
        "generic",
        "Action Proposals",
        "action_proposal_service",
        ("query",),
    ),
    (
        "generic",
        "Action Blockers",
        "action_blocker_service",
        ("list_blockers",),
    ),
    (
        "generic",
        "Action Proposal Reviews",
        "action_review_service",
        ("list_reviews",),
    ),
    (
        "generic",
        "Execution Handoffs",
        "execution_handoff_service",
        ("list_handoffs",),
    ),
    (
        "generic",
        "Tool Intent Reviews",
        "tool_intent_review_service",
        ("list_reviews",),
    ),
    (
        "generic",
        "Supervised Runs",
        "run_supervision_service",
        ("query",),
    ),
    (
        "generic",
        "Run Control Requests",
        "run_control_service",
        ("list_requests",),
    ),
    (
        "generic",
        "Compensation Plans",
        "compensation_planner",
        ("list_plans",),
    ),
    (
        "generic",
        "Unread Notifications",
        "notification_query_service",
        ("list_notifications",),
    ),
    (
        "generic",
        "Open Alerts",
        "alert_service",
        ("list_alerts",),
    ),
    (
        "generic",
        "Escalation Records",
        "escalation_service",
        ("list_records",),
    ),
    (
        "generic",
        "Notification Digests",
        "notification_digest_service",
        ("list_digests",),
    ),
    ("scheduler", "Active Schedules", "scheduler_service", ("list_schedules",)),
    ("scheduler", "Due Items", "scheduler_service", ("list_due_items",)),
    ("scheduler", "Open Reminders", "scheduler_service", ("list_reminders",)),
    ("scheduler", "Failed Tick Runs", "scheduler_service", ("list_tick_runs",)),
    ("incidents", "Open Incidents", "incident_service", ("list_incidents",)),
    ("root_causes", "Root Cause Candidates", "root_cause_service", ("list_candidates",)),
    ("recovery_reviews", "Recovery Reviews", "recovery_review_service", ("list_reviews",)),
    ("broken_references", "Broken References", "reference_validator", ("list_broken_references",)),
    (
        "orphaned_resources",
        "Orphaned Resources",
        "reference_validator",
        ("list_orphaned_resources",),
    ),
    ("registry_rebuilds", "Registry Rebuild Runs", "registry_rebuilder", ("list_runs",)),
    ("archive_candidates", "Archive Candidates", "archive_planner", ("list_candidates",)),
    (
        "redaction_candidates",
        "Redaction Candidates",
        "redaction_planner",
        ("list_candidates",),
    ),
    ("purge_previews", "Purge Previews", "purge_preview_service", ("list_previews",)),
    ("lifecycle_reviews", "Lifecycle Reviews", "lifecycle_review_service", ("list_reviews",)),
)

_RUNNING_STATUSES = {"running", "processing", "sending", "in_progress", "active"}
_PENDING_STATUSES = {
    "pending",
    "waiting_for_approval",
    "queued",
    "scheduled",
    "created",
    "proposed",
    "under_review",
    "approved_for_handoff",
}
_OPEN_AS_PENDING_QUEUE_TYPES: set[OperatorQueueType] = {
    "broken_references",
    "drift_findings",
    "incidents",
    "conformance_findings",
    "setup_findings",
    "rc_findings",
    "lifecycle_reviews",
    "migration_notes",
    "orphaned_resources",
    "purge_previews",
    "redaction_candidates",
}
_BLOCKED_STATUSES = {"blocked", "blocked_by_policy", "blocked_by_autonomy", "dead_lettered"}
_FAILED_STATUSES = {"failed", "error", "critical"}


class QueueSummaryBuilder:
    """Build read-only queue summaries."""

    def __init__(self, **providers: object) -> None:
        self._providers = providers

    def build_queues(self, scope: list[str]) -> list[OperatorQueueSummary]:
        """Build queue summaries from local service/repository contracts."""
        return [
            self._build_queue(queue_type, title, provider_key, methods, scope)
            for queue_type, title, provider_key, methods in _QUEUE_SPECS
        ]

    def _build_queue(
        self,
        queue_type: OperatorQueueType,
        title: str,
        provider_key: str,
        methods: tuple[str, ...],
        scope: list[str],
    ) -> OperatorQueueSummary:
        provider = self._providers.get(provider_key)
        if provider is None:
            return _summary(
                queue_type,
                title,
                0,
                0,
                0,
                0,
                "unknown",
                "medium",
                metadata={"available": False, "scope": scope},
            )
        try:
            items = _list_items(provider_key, provider, methods, scope)
        except Exception as exc:
            return _summary(
                queue_type,
                title,
                0,
                0,
                0,
                0,
                "unknown",
                "medium",
                metadata={"available": True, "error": exc.__class__.__name__},
            )
        pending, running, blocked, failed = _count_statuses(
            items,
            open_as_pending=queue_type in _OPEN_AS_PENDING_QUEUE_TYPES,
        )
        status = _queue_status(pending, running, blocked, failed)
        return _summary(
            queue_type,
            title,
            pending,
            running,
            blocked,
            failed,
            status,
            _severity(status),
            oldest_item_at=_oldest(items),
            newest_item_at=_newest(items),
            metadata={"available": True, "item_count": len(items)},
        )


def _summary(
    queue_type: OperatorQueueType,
    title: str,
    pending: int,
    running: int,
    blocked: int,
    failed: int,
    status: OperatorCardStatus,
    severity: OperatorSeverity,
    *,
    oldest_item_at: datetime | None = None,
    newest_item_at: datetime | None = None,
    metadata: dict[str, Any] | None = None,
) -> OperatorQueueSummary:
    return OperatorQueueSummary(
        queue_id=f"queue-{queue_type}",
        queue_type=queue_type,
        title=title,
        pending_count=pending,
        running_count=running,
        blocked_count=blocked,
        failed_count=failed,
        oldest_item_at=oldest_item_at,
        newest_item_at=newest_item_at,
        status=status,
        severity=severity,
        metadata=metadata or {},
    )


def _list_items(
    provider_key: str, provider: object, methods: tuple[str, ...], scope: list[str]
) -> list[object]:
    for name in methods:
        method = getattr(provider, name, None)
        if callable(method):
            if name == "list_requests":
                try:
                    from aion_brain.contracts.approvals import ApprovalInboxQuery

                    return list(
                        cast(Any, method)(
                            ApprovalInboxQuery(scope=scope or ["workspace:main"], limit=100)
                        )
                        or []
                    )
                except (ImportError, TypeError):
                    pass
            if name == "list_outputs":
                try:
                    from aion_brain.contracts.output_governance import ModelOutputQuery

                    return list(
                        cast(Any, method)(
                            ModelOutputQuery(
                                scope=scope or ["workspace:main"],
                                status="blocked",
                                limit=100,
                            )
                        )
                        or []
                    )
                except (ImportError, TypeError):
                    pass
            if name == "query":
                try:
                    if provider_key == "action_proposal_service":
                        from aion_brain.contracts.action_proposals import ActionProposalQuery

                        result = cast(Any, method)(
                            ActionProposalQuery(scope=scope or ["workspace:main"], limit=100)
                        )
                        return list(getattr(result, "proposals", []) or [])
                    return list(
                        cast(Any, method)(scope=scope or ["workspace:main"], limit=100) or []
                    )
                except (ImportError, TypeError):
                    pass
            return _call_list(method, scope)
    return []


def _call_list(method: object, scope: list[str]) -> list[object]:
    callable_method = cast(Any, method)
    attempts: tuple[dict[str, object], ...] = (
        {"scope": scope, "limit": 100},
        {"scope": scope},
        {"limit": 100},
        {},
    )
    for kwargs in attempts:
        try:
            value = callable_method(**kwargs)
            return list(value or [])
        except TypeError:
            continue
    return []


def _count_statuses(
    items: list[object],
    *,
    open_as_pending: bool = False,
) -> tuple[int, int, int, int]:
    pending = running = blocked = failed = 0
    for item in items:
        status = str(getattr(item, "status", "") or "").lower()
        if status in _PENDING_STATUSES or (open_as_pending and status == "open"):
            pending += 1
        elif status in _RUNNING_STATUSES:
            running += 1
        elif status in _BLOCKED_STATUSES:
            blocked += 1
        elif status in _FAILED_STATUSES:
            failed += 1
    return pending, running, blocked, failed


def _queue_status(
    pending: int,
    running: int,
    blocked: int,
    failed: int,
) -> OperatorCardStatus:
    if failed:
        return "failed"
    if blocked:
        return "blocked"
    if pending or running:
        return "warning"
    return "healthy"


def _severity(status: OperatorCardStatus) -> OperatorSeverity:
    if status == "failed":
        return "critical"
    if status == "blocked":
        return "high"
    if status in {"warning", "unknown"}:
        return "medium"
    return "low"


def _created_at(item: object) -> datetime | None:
    value = getattr(item, "created_at", None) or getattr(item, "updated_at", None)
    return value if isinstance(value, datetime) else None


def _oldest(items: list[object]) -> datetime | None:
    values = [value for value in (_created_at(item) for item in items) if value is not None]
    return min(values) if values else None


def _newest(items: list[object]) -> datetime | None:
    values = [value for value in (_created_at(item) for item in items) if value is not None]
    return max(values) if values else None
