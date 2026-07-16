from __future__ import annotations

from aion_brain.config import Settings
from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_request_identity_config_default_false_and_env_alias() -> None:
    assert Settings(_env_file=None).production_auth_request_boundary_enabled is False
    assert (
        Settings(
            _env_file=None,
            AION_PRODUCTION_AUTH_REQUEST_BOUNDARY_ENABLED=True,
        ).production_auth_request_boundary_enabled
        is True
    )


def test_request_identity_config_does_not_enable_runtime_auth() -> None:
    settings = Settings(
        _env_file=None,
        AION_PRODUCTION_AUTH_REQUEST_BOUNDARY_ENABLED=True,
    )

    assert settings.production_auth_enabled is False
    assert settings.auth_runtime_enabled is False
    assert settings.production_auth_core_runtime_enabled is False


def test_request_identity_diagnostics_are_redacted_and_disabled() -> None:
    container = kernel_container()
    checks = {
        check.name: check
        for check in KernelDiagnostics(container).run()
        if check.component == "production_auth_request_identity"
    }

    assert checks["request_identity_boundary_implemented"].status == "passed"
    assert checks["request_identity_boundary_default_disabled"].status == "passed"
    assert checks["request_identity_boundary_runtime_disabled"].status == "passed"
    assert checks["request_identity_boundary_diagnostics_redacted"].status == "passed"
