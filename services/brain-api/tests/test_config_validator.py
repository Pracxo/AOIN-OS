"""Runtime config validator tests."""

from __future__ import annotations

from aion_brain.contracts.runtime_config import ConfigValidationRequest
from tests.runtime_config_fakes import SCOPE, services, settings


def test_config_validator_fails_unsafe_external_model_default() -> None:
    *_, validator, _, _ = services(configured_settings=settings(AION_MODEL_GATEWAY_ENABLED=True))

    run = validator.validate(ConfigValidationRequest(owner_scope=SCOPE))

    assert run.status == "failed"
    assert any(check.name == "external_models_disabled_by_default" for check in run.checks)


def test_config_validator_fails_stacktrace_exposure() -> None:
    *_, validator, _, _ = services(configured_settings=settings(AION_API_STACKTRACE_EXPOSED=True))

    run = validator.validate(ConfigValidationRequest(owner_scope=SCOPE))

    assert run.status == "failed"
    assert any(check.name == "api_stacktrace_exposed_false" for check in run.checks)


def test_config_validator_warns_optional_adapter_unavailable() -> None:
    *_, validator, _, _ = services(configured_settings=settings(AION_SANDBOX_DOCKER_ENABLED=True))

    run = validator.validate(ConfigValidationRequest(owner_scope=SCOPE))

    assert any(check["name"] == "optional_adapters_remain_optional" for check in run.warnings)
