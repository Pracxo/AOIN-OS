"""Model gateway integration with provider hardening metadata."""

from __future__ import annotations

from tests.model_gateway_fakes import model_gateway_service
from tests.model_provider_hardening_helpers import repository


def test_model_gateway_provider_hardening_status_is_not_enablement() -> None:
    service, _repo, _policy, _telemetry = model_gateway_service()
    hardening_repo = repository()
    service.set_provider_hardening_repository(hardening_repo)

    status = service.provider_hardening_status()

    assert status["readiness_is_not_enablement"] is True
    assert status["external_model_calls_enabled"] is False
