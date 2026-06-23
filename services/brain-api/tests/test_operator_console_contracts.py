from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.operator_console import (
    ConsoleActionDescriptor,
    ConsoleAuditResult,
    ConsoleDataSource,
    ConsoleViewModel,
)


def test_console_view_model_read_only_must_be_true() -> None:
    with pytest.raises(ValidationError):
        ConsoleViewModel(
            console_view_model_id="console-view-1",
            view="overview",
            status="ready",
            read_only=False,
            owner_scope=["workspace:main"],
            title="Overview",
            summary="safe summary",
            sections=[],
            generated_at=datetime.now(UTC),
            redaction_applied=True,
        )


def test_console_view_model_redaction_must_be_true() -> None:
    with pytest.raises(ValidationError):
        ConsoleViewModel(
            console_view_model_id="console-view-1",
            view="overview",
            status="ready",
            read_only=True,
            owner_scope=["workspace:main"],
            title="Overview",
            summary="safe summary",
            sections=[],
            generated_at=datetime.now(UTC),
            redaction_applied=False,
        )


def test_forbidden_action_requires_reason() -> None:
    with pytest.raises(ValidationError):
        ConsoleActionDescriptor(
            action_key="activate_module",
            label="Activate Module",
            action_type="forbidden",
            status="forbidden",
            dry_run_only=False,
            forbidden=True,
            requires_policy=True,
            requires_approval=True,
            reason="",
        )


def test_console_data_source_read_only_must_be_true() -> None:
    with pytest.raises(ValidationError):
        ConsoleDataSource(
            data_source_id="overview.health",
            source_key="health",
            source_type="health",
            service_name="health",
            status="available",
            available=True,
            read_only=False,
            owner_scope=["workspace:main"],
        )


def test_console_audit_result_requires_frontend_absent() -> None:
    with pytest.raises(ValidationError):
        ConsoleAuditResult(
            console_audit_id="console-audit-1",
            status="failed",
            owner_scope=["workspace:main"],
            views_checked=["overview"],
            findings=[],
            redaction_passed=True,
            forbidden_action_passed=True,
            data_source_passed=True,
            frontend_absent=False,
            created_at=datetime.now(UTC),
        )
