from __future__ import annotations

import asyncio
from datetime import UTC, datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from aion_brain.contracts.request_identity import (
    RequestIdentityVerificationInput,
    RequestIdentityVerificationResult,
)
from aion_brain.kernel.container import KernelContainer
from aion_brain.production_auth.verifier import (
    DeterministicDisabledTestVerifier,
    DisabledRequestIdentityVerifier,
)
from tests.kernel_fakes import kernel_container

REPO_ROOT = Path(__file__).resolve().parents[3]
FIXED_NOW = datetime(2026, 7, 16, 10, 0, 0, tzinfo=UTC)


def test_disabled_verifier_returns_anonymous_disabled_result() -> None:
    verifier = DisabledRequestIdentityVerifier(
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )
    result = asyncio.run(
        verifier.verify(
            RequestIdentityVerificationInput(
                request_id="request-1",
                trace_id="trace-1",
                correlation_id="corr-1",
            )
        )
    )

    assert result.identity_source == "disabled_verifier"
    assert result.authentication_state == "disabled"
    assert result.authenticated is False
    assert result.actor_id is None
    assert result.subject is None
    assert result.roles == ()
    assert result.runtime_effect is False


def test_deterministic_disabled_test_verifier_stays_disabled() -> None:
    verifier = DeterministicDisabledTestVerifier(
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )
    first = asyncio.run(
        verifier.verify(RequestIdentityVerificationInput(request_id="request-1"))
    )
    second = asyncio.run(
        verifier.verify(RequestIdentityVerificationInput(request_id="request-1"))
    )

    assert first.identity_source == "deterministic_disabled_test_verifier"
    assert first.verification_id == second.verification_id
    assert first.fingerprint == second.fingerprint
    assert first.authenticated is False
    assert first.roles == ()


def test_verifiers_do_not_expose_auth_operational_methods() -> None:
    forbidden = {
        "authenticate",
        "login",
        "logout",
        "callback",
        "parse_token",
        "verify_token",
        "issue_token",
        "refresh_token",
        "persist_session",
        "create_cookie",
        "call_provider",
    }

    for verifier in (DisabledRequestIdentityVerifier(), DeterministicDisabledTestVerifier()):
        assert forbidden.isdisjoint(dir(verifier))


def test_verifier_source_does_not_access_http_material_or_io_clients() -> None:
    source = (
        REPO_ROOT / "services/brain-api/src/aion_brain/production_auth/verifier.py"
    ).read_text()

    forbidden_fragments = (
        ".headers",
        ".cookies",
        ".body",
        ".query_params",
        "request.headers",
        "request.cookies",
        "request.body",
        "request.query_params",
        "requests.",
        "httpx.",
        "aiohttp.",
        "urllib.request",
        "socket.",
    )
    for fragment in forbidden_fragments:
        assert fragment not in source


def test_unknown_verifier_cannot_return_authenticated_contract() -> None:
    with pytest.raises(ValidationError):
        RequestIdentityVerificationResult(
            verification_id="verification-1",
            request_id="request-1",
            authenticated=True,
            created_at=FIXED_NOW,
        )


def test_kernel_container_never_selects_deterministic_test_verifier() -> None:
    container: KernelContainer = kernel_container()

    assert isinstance(
        container.production_auth_request_identity_verifier,
        DisabledRequestIdentityVerifier,
    )
    assert not isinstance(
        container.production_auth_request_identity_verifier,
        DeterministicDisabledTestVerifier,
    )


def test_disabled_verifier_performance_smoke() -> None:
    verifier = DisabledRequestIdentityVerifier(
        clock=lambda: FIXED_NOW,
        id_factory=lambda prefix: f"{prefix}-fixed",
    )

    async def run_many() -> None:
        for index in range(1000):
            result = await verifier.verify(
                RequestIdentityVerificationInput(request_id=f"request-{index}")
            )
            assert result.authenticated is False

    asyncio.run(run_many())
