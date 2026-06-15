"""Default cognitive cycle templates."""

from datetime import UTC, datetime

from aion_brain.contracts.cycles import CognitiveCycleStep, CognitiveCycleTemplate


def build_wake_cycle_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default wake cycle template."""
    return _template(
        "cycle-template-wake-default",
        "Default wake cycle",
        "Prepare generic Brain context for a manual session.",
        "wake",
        scope,
        [
            _step("attention_review", "attention_review", "Review pending attention signals."),
            _step(
                "observability_summary",
                "observability_summary",
                "Read local observability summary.",
            ),
            _step("kernel_self_test", "kernel_self_test", "Run a local dry kernel self-test."),
        ],
    )


def build_review_cycle_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default review cycle template."""
    return _template(
        "cycle-template-review-default",
        "Default review cycle",
        "Review recent generic Brain records.",
        "review",
        scope,
        [
            _step("attention_review", "attention_review", "Review focus and attention state."),
            _step("memory_conflict_scan", "memory_conflict_scan", "Scan generic memory conflicts."),
            _step("regression_check", "regression_check", "Run regression only when requested."),
            _step("visual_snapshot", "visual_snapshot", "Create or preview a visual snapshot."),
        ],
    )


def build_sleep_consolidation_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default sleep consolidation template."""
    return _template(
        "cycle-template-sleep-default",
        "Default sleep consolidation cycle",
        "Run deterministic generic sleep consolidation.",
        "sleep_consolidation",
        scope,
        [
            _step("attention_review", "attention_review", "Review attention state."),
            _step("working_memory_sweep", "working_memory_sweep", "Sweep expired working memory."),
            _step("memory_decay", "memory_decay", "Recompute memory decay."),
            _step("memory_conflict_scan", "memory_conflict_scan", "Scan memory conflicts."),
            _step("memory_compaction", "memory_compaction", "Run deterministic memory compaction."),
            _step("reflection_create", "reflection_create", "Summarize reflection opportunities."),
            _step(
                "skill_candidate_create",
                "skill_candidate_create",
                "Create skill candidates only when explicitly requested.",
            ),
            _step("regression_check", "regression_check", "Run regression only when requested."),
            _step("visual_snapshot", "visual_snapshot", "Create or preview visual snapshot."),
            _step(
                "observability_summary",
                "observability_summary",
                "Record observability summary.",
            ),
        ],
    )


def build_maintenance_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default maintenance cycle template."""
    return _template(
        "cycle-template-maintenance-default",
        "Default maintenance cycle",
        "Run safe generic maintenance checks.",
        "maintenance",
        scope,
        [
            _step("approval_expiry", "approval_expiry", "Review expirable approvals."),
            _step(
                "workflow_heartbeat_review",
                "workflow_heartbeat_review",
                "Review local workflow heartbeats.",
            ),
            _step("kernel_self_test", "kernel_self_test", "Run local dry kernel self-test."),
        ],
    )


def build_shutdown_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default shutdown cycle template."""
    return _template(
        "cycle-template-shutdown-default",
        "Default shutdown cycle",
        "Summarize state before a manual shutdown.",
        "shutdown",
        scope,
        [
            _step(
                "working_memory_sweep",
                "working_memory_sweep",
                "Preview working memory cleanup.",
            ),
            _step("visual_snapshot", "visual_snapshot", "Create or preview visual snapshot."),
            _step("observability_summary", "observability_summary", "Read observability summary."),
        ],
    )


def build_active_cycle_template(scope: list[str]) -> CognitiveCycleTemplate:
    """Build the default active cycle template."""
    return _template(
        "cycle-template-active-default",
        "Default active cycle",
        "Review active cognitive state without executing external work.",
        "active",
        scope,
        [
            _step("attention_review", "attention_review", "Review active focus state."),
            _step(
                "working_memory_sweep",
                "working_memory_sweep",
                "Preview working memory cleanup.",
            ),
            _step("noop", "noop", "No-op active cycle placeholder."),
        ],
    )


def default_template_for_cycle(cycle_type: str, scope: list[str]) -> CognitiveCycleTemplate:
    """Return the default template for a cycle type."""
    builders = {
        "wake": build_wake_cycle_template,
        "active": build_active_cycle_template,
        "review": build_review_cycle_template,
        "sleep_consolidation": build_sleep_consolidation_template,
        "maintenance": build_maintenance_template,
        "shutdown": build_shutdown_template,
    }
    try:
        return builders[cycle_type](scope)
    except KeyError as exc:
        raise ValueError(f"unknown_cycle_type:{cycle_type}") from exc


def _template(
    template_id: str,
    name: str,
    description: str,
    cycle_type: str,
    scope: list[str],
    steps: list[CognitiveCycleStep],
) -> CognitiveCycleTemplate:
    now = datetime.now(UTC)
    return CognitiveCycleTemplate(
        cycle_template_id=template_id,
        name=name,
        description=description,
        cycle_type=cycle_type,  # type: ignore[arg-type]
        status="active",
        owner_scope=scope or ["workspace:main"],
        steps=steps,
        risk_level="medium",
        requires_approval=False,
        metadata={"default": True},
        created_by="aion-system",
        created_at=now,
        updated_at=now,
    )


def _step(step_id: str, step_type: str, description: str) -> CognitiveCycleStep:
    return CognitiveCycleStep(
        step_id=step_id,
        step_type=step_type,  # type: ignore[arg-type]
        description=description,
        enabled=True,
        required=step_type in {"working_memory_sweep", "memory_decay", "observability_summary"},
        risk_level="low",
        input_template={},
        metadata={},
    )
