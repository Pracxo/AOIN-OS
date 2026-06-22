"""Module contract test harness tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.module_developer.contract_tests import ModuleContractTestHarness
from aion_brain.module_developer.repository import ModuleDeveloperRepository
from tests.module_developer_fakes import package


def repository() -> ModuleDeveloperRepository:
    return ModuleDeveloperRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )


def test_contract_harness_creates_default_tests() -> None:
    repo = repository()
    pkg = repo.save_package(package())

    tests = ModuleContractTestHarness(repo).create_default_tests(pkg)

    assert {test.test_type for test in tests} >= {
        "schema_validation",
        "policy_gate",
        "risk_gate",
        "autonomy_gate",
        "dry_run_invocation",
        "error_contract",
    }


def test_contract_harness_run_is_dry_run_only() -> None:
    repo = repository()
    repo.save_package(package())

    run = ModuleContractTestHarness(repo).run_tests("pkg-1", dry_run=True)

    assert run.status == "passed"
    assert run.report["module_code_executed"] is False
