from __future__ import annotations

from test_secure_runtime_integration_program_charter import (
    AUTH_ID,
    CLOSEOUT_TASK,
    CURRENT_AUTH_ID,
    CURRENT_CLOSEOUT_TASK,
    CURRENT_IMPLEMENTATION_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    read_text,
)


def test_project_status_reconciles_current_secure_runtime_program_state() -> None:
    status = read_text("docs/project-status.md")

    assert "Current milestone: AION-235 sandboxed deterministic capability" in status
    assert "Current task: AION-236 capability-runtime operator evaluation" in status
    assert PROGRAM_ID in status
    assert AUTH_ID in status
    assert CURRENT_AUTH_ID in status
    assert "AION-232-SRI-0002" in status
    assert IMPLEMENTATION_TASK in status
    assert CLOSEOUT_TASK in status
    assert CURRENT_IMPLEMENTATION_TASK in status
    assert "AION-233" in status
    assert CURRENT_CLOSEOUT_TASK in status
    assert "AION-234" in status
    assert "model_output_triggered_execution_enabled=false" in status
    assert "external_connector_execution_enabled=false" in status
    assert "external_tool_execution_enabled=false" in status
    assert "public_network_access_enabled=false" in status
    assert "production_runtime_authorized=false" in status
    assert "v0.2 remains unreleased" in status


def test_architecture_and_policy_projection_are_current_not_stale() -> None:
    architecture = read_text("docs/architecture.md")
    policy = read_text("docs/policy-model.md")
    visual = read_text("docs/visual-brain.md")

    assert "final Git evidence reconciliation is recorded by PR #147" in architecture
    assert "Secure Runtime Integration" in architecture
    assert "AION-230-SRI-0001" in architecture
    assert "secure_runtime.session.start" in policy
    assert "planning only" in policy
    assert "Secure Runtime Integration" in visual
