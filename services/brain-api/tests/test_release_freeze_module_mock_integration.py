"""Release and freeze integration for module mock runtime."""

from __future__ import annotations

from aion_brain.freeze.gate import FreezeGateService
from aion_brain.module_mock_runtime import ModuleMockSimulator
from aion_brain.release_package.packager import ReleasePackager
from tests.kernel_fakes import AllowPolicy
from tests.module_mock_helpers import invocation_request, settings
from tests.module_mock_helpers import repository as mock_repository


def test_release_package_module_mock_summary_is_metadata_only() -> None:
    repo = mock_repository()
    simulator = ModuleMockSimulator(repo, AllowPolicy(), settings=settings())
    simulator.invoke(invocation_request("missing-binding"))
    packager = ReleasePackager(
        repository=object(),  # type: ignore[arg-type]
        policy_adapter=AllowPolicy(),  # type: ignore[arg-type]
        module_mock_repository=repo,
        settings=settings(),
    )

    summary = packager._module_mock_summary(["workspace:main"])  # noqa: SLF001

    assert summary["module_mock_run_count"] == 1
    assert summary["activation_allowed"] is False
    assert summary["execution_allowed"] is False
    assert summary["external_calls_allowed"] is False
    assert summary["code_loading_allowed"] is False


def test_freeze_gate_module_mock_check_reports_blocked_records() -> None:
    repo = mock_repository()
    simulator = ModuleMockSimulator(repo, AllowPolicy(), settings=settings())
    simulator.invoke(invocation_request("missing-binding"))
    gate = FreezeGateService(  # type: ignore[call-arg]
        repository=object(),
        policy_adapter=AllowPolicy(),
        version_manifest_service=object(),
        feature_registry_service=object(),
        compatibility_matrix_service=object(),
        migration_baseline_service=object(),
        release_artifact_service=object(),
        sdk_compatibility_service=object(),
        settings=settings(),
    )
    gate.set_module_mock_repository(repo)

    check = gate._check_module_mock_runtime_safe()  # noqa: SLF001

    assert check["status"] == "failed"
    assert check["details"]["blocked_run_count"] == 1
