"""Model provider readiness tests."""

from __future__ import annotations

from tests.model_provider_hardening_helpers import readiness_request, services


def test_model_provider_readiness_keeps_external_and_credentials_false() -> None:
    readiness_service = services()["readiness_service"]

    readiness = readiness_service.assess(readiness_request())  # type: ignore[attr-defined]

    assert readiness.external_call_ready is False
    assert readiness.credentials_ready is False
    assert readiness.readiness_level == "dry_run_ready"


def test_model_provider_readiness_blocks_external_model_calls_enabled() -> None:
    readiness_service = services(AION_EXTERNAL_MODEL_CALLS_ENABLED=True)["readiness_service"]

    readiness = readiness_service.assess(readiness_request())  # type: ignore[attr-defined]

    assert readiness.status == "blocked"
    assert readiness.blocker_refs
