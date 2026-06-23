from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.local_auth import (
    LocalAuthAuditResult,
    LocalAuthContext,
    LocalOperatorIdentity,
)


def test_local_operator_identity_rejects_production_identity() -> None:
    with pytest.raises(ValidationError):
        LocalOperatorIdentity(
            local_identity_id="local-identity-1",
            actor_id="local.operator",
            workspace_id="local",
            display_name="Local Operator",
            roles=["operator"],
            owner_scope=["workspace:main"],
            status="simulated",
            identity_source="local_dev",
            production_identity=True,
            credentials_present=False,
        )


def test_local_auth_context_rejects_privileged_flags() -> None:
    with pytest.raises(ValidationError):
        LocalAuthContext(
            local_auth_context_id="local-auth-context-1",
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            read_allowed=True,
            dry_run_allowed=True,
            review_allowed=False,
            write_allowed=False,
            execute_allowed=True,
            activation_allowed=False,
            external_calls_allowed=False,
            production_auth=False,
            session_present=False,
            credentials_present=False,
        )


def test_local_auth_audit_result_requires_safe_booleans() -> None:
    with pytest.raises(ValidationError):
        LocalAuthAuditResult(
            local_auth_audit_id="local-auth-audit-1",
            status="failed",
            owner_scope=["workspace:main"],
            checks_run=["production_auth_disabled"],
            findings=[],
            production_auth_absent=False,
            credentials_absent=True,
            sessions_absent=True,
            external_identity_absent=True,
            write_actions_disabled=True,
            execution_disabled=True,
            activation_disabled=True,
            created_at=datetime.now(UTC),
        )
