"""Read-only workflow maps for future Operator Console views."""

from __future__ import annotations

from typing import cast

from aion_brain.contracts.operator_console import (
    ConsoleView,
    ConsoleWorkflowMap,
    ConsoleWorkflowStep,
)


def console_workflows(scope: list[str]) -> list[ConsoleWorkflowMap]:
    """Return deterministic console workflow maps."""
    return [
        ConsoleWorkflowMap(
            workflow_key="operator.first_run_readiness",
            title="First-run readiness",
            description="Inspect local readiness without installing packages or calling services.",
            status="read_only",
            owner_scope=scope,
            steps=[
                _step("setup_doctor", "Setup doctor", "readiness", "setup_doctor"),
                _step("golden_path", "Golden Path", "golden_path", "golden_path"),
                _step("overview", "Operator overview", "overview", "operator_overview"),
            ],
            no_go_conditions=["failing readiness", "secret display risk"],
        ),
        ConsoleWorkflowMap(
            workflow_key="operator.module_lifecycle",
            title="Module lifecycle review",
            description="Review metadata-only module lifecycle state without activation.",
            status="read_only",
            owner_scope=scope,
            steps=[
                _step("extensions", "Extension intake", "module_lifecycle", "extensions"),
                _step("bindings", "Capability bindings", "module_lifecycle", "module_bindings"),
                _step(
                    "activation_gate",
                    "Activation gate",
                    "module_activation",
                    "module_activation",
                ),
                _step("mock_runtime", "Mock runtime", "module_mock_runtime", "module_mock_runtime"),
            ],
            no_go_conditions=["activation enabled", "code loading enabled"],
        ),
        ConsoleWorkflowMap(
            workflow_key="operator.provider_hardening",
            title="Provider hardening review",
            description="Review provider readiness without prompt transmission or model calls.",
            status="read_only",
            owner_scope=scope,
            steps=[
                _step(
                    "profile",
                    "Provider profile",
                    "model_provider_hardening",
                    "model_provider_profiles",
                ),
                _step(
                    "egress",
                    "Prompt egress preview",
                    "model_provider_hardening",
                    "prompt_egress",
                ),
                _step(
                    "readiness",
                    "Provider readiness",
                    "model_provider_hardening",
                    "provider_readiness",
                ),
            ],
            no_go_conditions=["external calls enabled", "credential display risk"],
        ),
    ]


def console_demo_map(scope: list[str]) -> dict[str, object]:
    """Return the local demo map for future console consumers."""
    return {
        "demo_key": "operator.console.local_read_only",
        "owner_scope": scope,
        "read_only": True,
        "commands": [
            "./scripts/setup-doctor.sh --fast --offline-ok",
            "./scripts/golden-path.sh --offline-ok",
            "./scripts/rc-check.sh --offline-ok",
            "./scripts/module-pack-check.sh",
            "./scripts/generic-knowledge-demo.sh --offline-ok --skip-api",
            "./scripts/model-provider-check.sh --offline-ok --skip-api",
            "./scripts/demo-local.sh --offline-ok",
        ],
        "forbidden": ["activation", "execution", "external_calls", "frontend_runtime"],
    }


def _step(
    step_key: str,
    title: str,
    view: str,
    source_key: str,
) -> ConsoleWorkflowStep:
    return ConsoleWorkflowStep(
        step_key=step_key,
        title=title,
        view=cast(ConsoleView, view),
        source_key=source_key,
        cli_hint=None,
        endpoint_hint=None,
        expected_status="available",
        allowed_actions=["read", "dry_run"],
        forbidden_actions=["activate_module", "execute_tool", "enable_external_model_calls"],
        metadata={"read_only": True},
    )


__all__ = ["console_demo_map", "console_workflows"]
