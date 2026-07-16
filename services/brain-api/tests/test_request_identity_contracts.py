from __future__ import annotations

from datetime import UTC, datetime

import pytest
from pydantic import ValidationError

from aion_brain.contracts.request_identity import (
    REQUIRED_REASON_CODES,
    RequestIdentityAuditEvent,
    RequestIdentityBoundaryStatus,
    RequestIdentityContext,
    RequestIdentityVerificationInput,
    RequestIdentityVerificationResult,
)
from aion_brain.production_auth.canonical import sha256_fingerprint

FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_request_identity_contracts_accept_disabled_anonymous_defaults() -> None:
    verification = RequestIdentityVerificationResult(
        verification_id="verification-1",
        request_id="request-1",
        trace_id="trace-1",
        correlation_id="corr-1",
        created_at=FIXED_NOW,
    )

    assert verification.authorization_transaction_id == "AION-155-PA-0003"
    assert verification.implementation_task == "AION-156"
    assert verification.authorization_scope == "disabled-request-identity-boundary"
    assert verification.authentication_state == "disabled"
    assert verification.authenticated is False
    assert verification.actor_id is None
    assert verification.subject is None
    assert verification.roles == ()
    assert verification.runtime_effect is False
    assert verification.redacted is True
    assert verification.reason_codes == REQUIRED_REASON_CODES


def test_request_identity_contracts_reject_unknown_fields_and_versions() -> None:
    with pytest.raises(ValidationError):
        RequestIdentityVerificationInput(request_id="request-1", unexpected=True)

    with pytest.raises(ValidationError):
        RequestIdentityVerificationInput(
            request_id="request-1",
            schema_version="request-identity/v2",
        )

    with pytest.raises(ValidationError):
        RequestIdentityVerificationInput(
            request_id="request-1",
            boundary_version="request-identity-boundary/v2",
        )


def test_request_identity_contracts_reject_runtime_identity_state() -> None:
    base = {
        "verification_id": "verification-1",
        "request_id": "request-1",
        "created_at": FIXED_NOW,
    }

    for patch in (
        {"authenticated": True},
        {"actor_id": "actor-1"},
        {"subject": "subject-1"},
        {"roles": ("admin",)},
        {"runtime_effect": True},
        {"redacted": False},
    ):
        with pytest.raises(ValidationError):
            RequestIdentityVerificationResult(**{**base, **patch})


def test_request_identity_contracts_reject_unknown_reason_codes() -> None:
    with pytest.raises(ValidationError):
        RequestIdentityAuditEvent(
            event_id="event-1",
            event_type="request_identity_boundary_attached",
            request_id="request-1",
            reason_codes=("unknown_reason",),
            created_at=FIXED_NOW,
        )


def test_request_identity_fingerprint_is_self_excluding_and_enforced() -> None:
    context = RequestIdentityContext(
        context_id="context-1",
        verification_id="verification-1",
        request_id="request-1",
        trace_id="trace-1",
        correlation_id="corr-1",
        created_at=FIXED_NOW,
    )
    expected = sha256_fingerprint(context.model_dump(mode="json", exclude={"fingerprint"}))

    assert context.fingerprint == expected
    with pytest.raises(ValidationError):
        RequestIdentityContext(
            context_id="context-1",
            verification_id="verification-1",
            request_id="request-1",
            created_at=FIXED_NOW,
            fingerprint="0" * 64,
        )


def test_request_identity_boundary_status_holds_runtime_disabled() -> None:
    status = RequestIdentityBoundaryStatus(
        status_id="status-1",
        request_identity_boundary_registered=True,
        created_at=FIXED_NOW,
    )

    assert status.request_identity_boundary_implemented is True
    assert status.request_identity_boundary_state == "implemented_disabled"
    assert status.request_identity_boundary_default_enabled is False
    assert status.request_identity_boundary_registered is True
    assert status.identity_verification_enabled is False
    assert status.authenticated_requests_enabled is False
    assert status.production_auth_runtime_enabled is False
