"""Freeze gate security hardening integration tests."""

from __future__ import annotations

from aion_brain.contracts.freeze import FreezeGateRunRequest
from tests.kernel_fakes import kernel_container
from tests.resilience_fakes import test_run as resilience_test_run


def test_freeze_gate_includes_hardening_check() -> None:
    container = kernel_container()
    container.freeze_gate_service._resilience_test_runner = FakeResilienceRunner()  # noqa: SLF001
    run = container.freeze_gate_service.run(
        FreezeGateRunRequest(
            version="0.1.0",
            owner_scope=["workspace:main"],
            include_contract_export=False,
            include_sdk_check=False,
            include_migration_baseline=False,
            include_release_baseline=False,
            include_kernel_self_test=False,
            include_policy_coverage=False,
            include_openapi_hygiene=False,
            include_boundary_check=False,
            include_no_domain_drift=False,
            include_repo_health=False,
            dry_run=True,
        )
    )

    assert any(check.name == "security_hardening_gate_passed" for check in run.checks)


class FakeResilienceRunner:
    def run(self, request: object) -> object:
        return resilience_test_run()
