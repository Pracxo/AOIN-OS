"""Read-only Operator Console action descriptors."""

from __future__ import annotations

from typing import cast

from aion_brain.contracts.operator_console import ConsoleActionDescriptor, ConsoleActionType


def allowed_action_descriptors() -> list[ConsoleActionDescriptor]:
    """Return descriptive safe actions. These descriptors never execute."""
    return [
        _allowed("run_dry_run_check", "Run dry-run check", "dry_run"),
        _allowed("acknowledge_notification", "Acknowledge notification", "acknowledge"),
        _allowed(
            "dismiss_non_blocking_finding_with_reason",
            "Dismiss non-blocking finding with reason",
            "dismiss_with_reason",
        ),
        _allowed("create_review_record", "Create operator review record", "review_record"),
        _allowed("inspect_refs", "Inspect refs", "read"),
        _allowed("export_redacted_summary", "Export redacted summary", "read"),
    ]


def forbidden_action_descriptors() -> list[ConsoleActionDescriptor]:
    """Return actions forbidden for AION-088 console view models."""
    reasons = {
        "activate_module": "Module activation remains disabled.",
        "activate_capability": "Capability activation remains disabled.",
        "load_code": "Code loading is outside the AION-088 boundary.",
        "install_package": "Package installation is outside the AION-088 boundary.",
        "register_route": "Runtime route registration is forbidden.",
        "enable_external_model_calls": "External model calls remain disabled.",
        "store_credentials": "Credential storage is forbidden.",
        "execute_tool": "Tool execution is forbidden.",
        "execute_handoff": "Controlled handoff execution is forbidden.",
        "bypass_policy": "Policy gates must not be bypassed.",
        "hard_delete": "Hard delete remains disabled.",
        "reveal_raw_prompt": "Prompt bodies must not be exposed.",
        "reveal_hidden_reasoning": "Private trace content must not be exposed.",
        "reveal_secret": "Secrets must not be exposed.",
    }
    labels = {
        "reveal_raw_prompt": "Reveal Source Text",
        "reveal_hidden_reasoning": "Reveal Private Trace",
        "reveal_secret": "Reveal Protected Value",
    }
    return [
        ConsoleActionDescriptor(
            action_key=key,
            label=labels.get(key, key.replace("_", " ").title()),
            action_type="forbidden",
            status="forbidden",
            dry_run_only=False,
            forbidden=True,
            requires_policy=True,
            requires_approval=True,
            reason=reason,
            metadata={"descriptor_only": True},
        )
        for key, reason in reasons.items()
    ]


def sensitive_view_forbidden_actions() -> list[ConsoleActionDescriptor]:
    """Return forbidden actions required in sensitive views."""
    return forbidden_action_descriptors()


def _allowed(action_key: str, label: str, action_type: str) -> ConsoleActionDescriptor:
    return ConsoleActionDescriptor(
        action_key=action_key,
        label=label,
        action_type=cast(ConsoleActionType, action_type),
        status="available",
        dry_run_only=action_type != "read",
        forbidden=False,
        requires_policy=True,
        requires_approval=action_type in {"dismiss_with_reason", "review_record"},
        reason="",
        metadata={"descriptor_only": True},
    )


__all__ = [
    "allowed_action_descriptors",
    "forbidden_action_descriptors",
    "sensitive_view_forbidden_actions",
]
