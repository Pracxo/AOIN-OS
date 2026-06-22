"""Default bounded retry policies for generic AION targets."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.resilience import RetryPolicy, RetryPolicyTargetType

DEFAULT_RETRY_POLICY_SPECS: tuple[tuple[str, RetryPolicyTargetType, str], ...] = (
    ("command_standard", "command", "Bounded command retry metadata."),
    ("outbox_standard", "outbox", "Bounded outbox delivery retry metadata."),
    ("workflow_standard", "workflow", "Bounded workflow retry metadata."),
    ("model_gateway_standard", "model_gateway", "Bounded model gateway retry metadata."),
    ("memory_adapter_standard", "memory_adapter", "Bounded memory adapter retry metadata."),
    ("graph_adapter_standard", "graph_adapter", "Bounded graph adapter retry metadata."),
    ("mcp_standard", "mcp", "Bounded MCP retry metadata."),
)


def default_retry_policies(owner_scope: list[str] | None = None) -> list[RetryPolicy]:
    """Return default retry policies without persistence side effects."""
    scope = owner_scope or ["workspace:main"]
    now = datetime.now(UTC)
    return [
        RetryPolicy(
            retry_policy_id=f"retry-policy-{name.replace('_', '-')}",
            name=name,
            description=description,
            status="active",
            target_type=target_type,
            max_attempts=3,
            initial_delay_ms=1000,
            max_delay_ms=30000,
            backoff_multiplier=2.0,
            jitter_enabled=False,
            retryable_statuses=["timeout", "unavailable", "failed", "degraded"],
            non_retryable_statuses=["blocked_by_policy", "validation_error", "disabled"],
            owner_scope=scope,
            metadata={"source": "aion_defaults"},
            created_by=None,
            created_at=now,
            updated_at=now,
            disabled_at=None,
        )
        for name, target_type, description in DEFAULT_RETRY_POLICY_SPECS
    ]
