from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.local_session import (
    LocalSessionAuditResult,
    LocalSessionContext,
    LocalSessionPreview,
)


def _preview(**updates: object) -> LocalSessionPreview:
    payload = {
        "local_session_preview_id": "local-session-preview-1",
        "actor_id": "local.operator",
        "workspace_id": "local",
        "roles": ["operator"],
        "owner_scope": ["workspace:main"],
        "status": "active_local_preview",
        "session_type": "local_preview",
        "read_only": True,
        "dev_only": True,
        "production_session": False,
        "credential_backed": False,
        "token_issued": False,
        "cookie_issued": False,
        "persistent": False,
        "write_allowed": False,
        "execute_allowed": False,
        "activation_allowed": False,
        "external_calls_allowed": False,
    }
    payload.update(updates)
    return LocalSessionPreview(**payload)


def test_local_session_preview_requires_safe_flags() -> None:
    assert _preview().read_only is True
    for key in [
        "production_session",
        "credential_backed",
        "token_issued",
        "cookie_issued",
        "persistent",
        "write_allowed",
        "execute_allowed",
        "activation_allowed",
        "external_calls_allowed",
    ]:
        with pytest.raises(ValidationError):
            _preview(**{key: True})


def test_local_session_context_rejects_privileged_flags() -> None:
    with pytest.raises(ValidationError):
        LocalSessionContext(
            local_session_preview_id="local-session-preview-1",
            actor_id="local.operator",
            workspace_id="local",
            roles=["operator"],
            owner_scope=["workspace:main"],
            read_allowed=True,
            dry_run_allowed=True,
            review_allowed=False,
            write_allowed=True,
            execute_allowed=False,
            activation_allowed=False,
            external_calls_allowed=False,
            session_valid=True,
            session_read_only=True,
        )


def test_local_session_audit_result_requires_safe_booleans_for_passed_status() -> None:
    with pytest.raises(ValidationError):
        LocalSessionAuditResult(
            local_session_audit_id="local-session-audit-1",
            status="passed",
            owner_scope=["workspace:main"],
            checks_run=["credentials_absent"],
            findings=[],
            sessions_are_dev_only=True,
            sessions_are_read_only=True,
            credentials_absent=False,
            tokens_absent=True,
            cookies_absent=True,
            persistence_absent=True,
            production_auth_absent=True,
            write_actions_disabled=True,
            execution_disabled=True,
            activation_disabled=True,
            external_calls_disabled=True,
            created_at=datetime.now(UTC),
        )
