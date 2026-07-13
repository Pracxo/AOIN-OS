from __future__ import annotations

import pytest
from pydantic import ValidationError

from aion_brain.config import Settings
from aion_brain.contracts.production_auth import ProductionAuthCoreConfig
from aion_brain.kernel.diagnostics import KernelDiagnostics
from tests.kernel_fakes import kernel_container


def test_repeated_service_and_diagnostic_construction_has_no_shared_mutable_state() -> None:
    first = kernel_container().production_auth_core_service
    second = kernel_container().production_auth_core_service

    first_snapshot = first.diagnostic_snapshot()
    second_snapshot = second.diagnostic_snapshot()

    assert first is not second
    assert first_snapshot.runtime_enabled is False
    assert second_snapshot.runtime_enabled is False
    assert id(first_snapshot.metadata) != id(second_snapshot.metadata)


def test_settings_mapping_is_deterministic_and_fails_closed_when_runtime_true() -> None:
    settings = Settings(_env_file=None)

    assert ProductionAuthCoreConfig.from_settings(settings).model_dump() == (
        ProductionAuthCoreConfig.from_settings(settings).model_dump()
    )

    with pytest.raises(ValidationError):
        ProductionAuthCoreConfig.from_settings(
            Settings(_env_file=None, AION_PRODUCTION_AUTH_ENABLED=True)
        )


def test_kernel_diagnostics_keep_production_auth_runtime_disabled() -> None:
    checks = {
        check.name: check
        for check in KernelDiagnostics(kernel_container()).run()
        if check.component == "production_auth_core"
    }

    assert checks["production_auth_core_implemented"].status == "passed"
    assert checks["production_auth_core_runtime_disabled"].status == "passed"
    assert checks["production_auth_core_guard_hold_active"].status == "passed"
    assert checks["production_auth_core_diagnostics_redacted"].status == "passed"
