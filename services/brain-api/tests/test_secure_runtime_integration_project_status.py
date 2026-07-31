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

    assert "AION-230 Secure Runtime Integration Program authorized" in status
    assert "AION-231 controlled authenticated local operator runtime foundation" in status
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
    assert "active_glm_implementation_authorization_count=0" in status
    assert "provider network egress remains disabled" in status
    assert "connectors remain disabled" in status
    assert "tools remain disabled" in status
    assert "modules remain disabled" in status
    assert "production runtime remains disabled" in status
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
