"""Security baseline integration for module mock runtime."""

from __future__ import annotations

from aion_brain.security_baseline.hardening_gate import HardeningGateService
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import repository as mock_repository
from tests.module_mock_helpers import settings


def test_security_baseline_confirms_module_mock_execution_paths_disabled() -> None:
    service = HardeningGateService(  # type: ignore[call-arg]
        repository=object(),
        policy_adapter=AllowPolicy(),
        secret_scanner=object(),
        config_checker=object(),
        api_exposure_checker=object(),
        adapter_risk_checker=object(),
        dependency_metadata_scanner=object(),
        threat_model_service=object(),
        security_control_catalog=object(),
        settings=settings(),
    )
    service.set_module_mock_repository(mock_repository())

    checks = service._module_mock_checks()  # noqa: SLF001
    by_name = {check["name"]: check for check in checks}

    assert by_name["module_mock_code_loading_disabled"]["status"] == "passed"
    assert by_name["module_mock_external_calls_disabled"]["status"] == "passed"
    assert by_name["module_mock_controlled_execution_disabled"]["status"] == "passed"
