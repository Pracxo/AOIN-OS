"""Module certifier tests."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.module_developer.repository import ModuleDeveloperRepository
from tests.module_developer_fakes import (
    AllowPolicy,
    DenyPolicy,
    FakeRuntimeGateway,
    FakeTelemetry,
    certifier,
    manifest,
    package_request,
)


def repository() -> ModuleDeveloperRepository:
    return ModuleDeveloperRepository(
        engine=create_engine(
            "sqlite+pysqlite:///:memory:",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
    )


def test_certifier_calls_policy_before_certify() -> None:
    repo = repository()
    policy = AllowPolicy()
    service = certifier(repo, policy=policy)
    pkg = service.submit_package(package_request())

    service.certify(
        __import__(
            "aion_brain.contracts.module_developer",
            fromlist=["ModuleCertificationRequest"],
        ).ModuleCertificationRequest(
            module_package_id=pkg.module_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert any(request.action_type == "module.package.certify" for request in policy.requests)


def test_policy_deny_blocks_certification() -> None:
    repo = repository()
    allow = certifier(repo)
    pkg = allow.submit_package(package_request())
    denied = certifier(repo, policy=DenyPolicy())

    with pytest.raises(PermissionError):
        denied.certify(
            __import__(
                "aion_brain.contracts.module_developer",
                fromlist=["ModuleCertificationRequest"],
            ).ModuleCertificationRequest(
                module_package_id=pkg.module_package_id,
                owner_scope=["workspace:main"],
            )
        )


def test_certifier_creates_certification_run() -> None:
    repo = repository()
    runtime = FakeRuntimeGateway()
    service = certifier(repo, runtime_gateway=runtime)
    pkg = service.submit_package(package_request())

    run = service.certify(
        __import__(
            "aion_brain.contracts.module_developer",
            fromlist=["ModuleCertificationRequest"],
        ).ModuleCertificationRequest(
            module_package_id=pkg.module_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.total_checks > 0
    assert run.report["module_code_executed"] is False
    assert runtime.certified == ["generic.example.echo"]


def test_certifier_does_not_execute_module_code() -> None:
    repo = repository()
    runtime = FakeRuntimeGateway()
    service = certifier(repo, runtime_gateway=runtime)
    pkg = service.submit_package(package_request())

    service.certify(
        __import__(
            "aion_brain.contracts.module_developer",
            fromlist=["ModuleCertificationRequest"],
        ).ModuleCertificationRequest(
            module_package_id=pkg.module_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert runtime.invoked is False


def test_certifier_fails_package_with_critical_validation_failure() -> None:
    repo = repository()
    bad_manifest = manifest(capabilities=[{"capability_id": "generic.example.bad"}])
    service = certifier(repo)
    pkg = service.submit_package(package_request(manifest=bad_manifest))

    run = service.certify(
        __import__(
            "aion_brain.contracts.module_developer",
            fromlist=["ModuleCertificationRequest"],
        ).ModuleCertificationRequest(
            module_package_id=pkg.module_package_id,
            owner_scope=["workspace:main"],
        )
    )

    assert run.status == "failed"


def test_certifier_emits_visual_telemetry_events() -> None:
    repo = repository()
    telemetry = FakeTelemetry()
    service = certifier(repo, telemetry=telemetry)
    pkg = service.submit_package(package_request())
    service.certify(
        __import__(
            "aion_brain.contracts.module_developer",
            fromlist=["ModuleCertificationRequest"],
        ).ModuleCertificationRequest(
            module_package_id=pkg.module_package_id,
            owner_scope=["workspace:main"],
        )
    )

    event_types = {getattr(event, "event_type", None) for event in telemetry.events}
    assert "module_package_submitted" in event_types
    assert "module_certification_started" in event_types
    assert "module_certification_completed" in event_types
