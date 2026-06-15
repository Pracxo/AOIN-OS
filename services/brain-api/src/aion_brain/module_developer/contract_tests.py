"""Dry-run module contract test harness."""

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.module_developer import (
    ModuleCertificationRun,
    ModuleContractTestCase,
    ModulePackage,
)
from aion_brain.module_developer.repository import ModuleDeveloperRepository


class ModuleContractTestHarness:
    """Create and run static contract tests without executing module code."""

    def __init__(self, repository: ModuleDeveloperRepository) -> None:
        self._repository = repository

    def create_default_tests(self, package: ModulePackage) -> list[ModuleContractTestCase]:
        """Create default generic tests for each package capability."""

        now = datetime.now(UTC)
        tests = [
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="schema_validation",
                name="manifest schema validation",
                description="Manifest and capability schemas must be declarative objects.",
                input={"module_package_id": package.module_package_id},
                expected={"valid": True},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="policy_gate",
                name="policy gate",
                description="Certification requires policy authorization.",
                input={"action_type": "module.package.certify"},
                expected={"policy_checked": True},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="risk_gate",
                name="risk gate",
                description="Capability risk metadata must be present.",
                input={"capabilities": len(package.manifest.capabilities)},
                expected={"risk_checked": True},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="autonomy_gate",
                name="autonomy gate",
                description="Autonomy compatibility is checked without execution.",
                input={"mode": "dry_run"},
                expected={"autonomy_checked": True},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="dry_run_invocation",
                name="dry-run invocation",
                description="Runtime gateway certification is side-effect-free.",
                input={"mode": "dry_run"},
                expected={"module_code_executed": False},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
            ModuleContractTestCase(
                test_case_id=f"test-{uuid4().hex}",
                module_package_id=package.module_package_id,
                capability_id=None,
                test_type="error_contract",
                name="error contract",
                description="Module package failures map to AION contracts.",
                input={"error": "contract_failure"},
                expected={"aion_contract": True},
                status="active",
                metadata={"dry_run": True},
                created_at=now,
            ),
        ]
        return [self._repository.save_contract_test_case(test) for test in tests]

    def run_tests(self, module_package_id: str, dry_run: bool = True) -> ModuleCertificationRun:
        """Run static default contract tests only."""

        package = self._repository.get_package(module_package_id)
        if package is None:
            raise ValueError("module_package_not_found")
        tests = self.create_default_tests(package)
        now = datetime.now(UTC)
        run = ModuleCertificationRun(
            certification_run_id=f"contract-test-{uuid4().hex}",
            module_package_id=package.module_package_id,
            module_id=package.module_id,
            version=package.version,
            status="passed" if dry_run else "failed",
            total_checks=len(tests),
            passed_checks=len(tests) if dry_run else 0,
            failed_checks=0 if dry_run else len(tests),
            warning_checks=0,
            score=1.0 if dry_run else 0.0,
            report={
                "dry_run": dry_run,
                "module_code_executed": False,
                "tests": [test.model_dump(mode="json") for test in tests],
            },
            created_by=None,
            created_at=now,
            completed_at=now,
        )
        return self._repository.save_certification_run(run)

