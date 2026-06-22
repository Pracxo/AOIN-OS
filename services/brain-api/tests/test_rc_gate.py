"""Release candidate gate service tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.config import Settings
from aion_brain.contracts.operator import OperatorOverviewRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.release_candidate import RCGateRunRequest
from aion_brain.contracts.verification_matrix import (
    VerificationCheck,
    VerificationMatrixCreateRequest,
)
from aion_brain.release_candidate.candidates import ReleaseCandidateService
from aion_brain.release_candidate.checks import VerificationCheckCollector
from aion_brain.release_candidate.evidence_pack import RCEvidencePackService
from aion_brain.release_candidate.findings import RCFindingService
from aion_brain.release_candidate.gate import RCGateService
from aion_brain.release_candidate.matrix import VerificationMatrixService
from aion_brain.release_candidate.reports import RCReportService
from aion_brain.release_candidate.repository import ReleaseCandidateRepository


class AllowPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class ReadyWarningFreezeGate:
    def run(self, request: object) -> object:
        return {
            "status": "warning",
            "failures": [],
            "report": {"release_ready": True},
            "request": request.__class__.__name__,
        }


class FakeOperatorService:
    def overview(
        self, request: OperatorOverviewRequest, *, actor_context: object | None = None
    ) -> dict[str, object]:
        assert actor_context is not None
        return {"owner_scope": request.owner_scope, "overall_status": "ready"}


def test_rc_gate_passes_when_required_checks_pass() -> None:
    services = _services(AllowPolicy())
    matrix = services["matrix"].create_matrix(
        VerificationMatrixCreateRequest(
            matrix_key="rc.test",
            version="0.1.0",
            owner_scope=["workspace:main"],
            required_checks=["tests.brain"],
            optional_checks=[],
            release_ready_threshold=0.95,
        )
    )

    run = services["gate"].run(
        RCGateRunRequest(
            verification_matrix_id=matrix.verification_matrix_id,
            owner_scope=["workspace:main"],
            run_service_checks=False,
            check_results=[_check("tests.brain", "passed")],
        )
    )

    assert run.status == "passed"
    assert run.release_ready is True
    assert run.evidence_pack_id is not None
    assert services["repository"].list_reports()[0].release_ready is True


def test_rc_gate_creates_blocking_finding_for_failed_required_check() -> None:
    services = _services(AllowPolicy())
    matrix = services["matrix"].create_matrix(
        VerificationMatrixCreateRequest(
            matrix_key="rc.failed",
            version="0.1.0",
            owner_scope=["workspace:main"],
            required_checks=["tests.brain"],
            optional_checks=[],
        )
    )

    run = services["gate"].run(
        RCGateRunRequest(
            verification_matrix_id=matrix.verification_matrix_id,
            owner_scope=["workspace:main"],
            run_service_checks=False,
            check_results=[_check("tests.brain", "failed")],
        )
    )

    assert run.status == "blocked"
    assert run.release_ready is False
    assert run.findings[0].blocking is True


def test_rc_gate_does_not_penalize_skipped_optional_checks() -> None:
    services = _services(AllowPolicy())
    matrix = services["matrix"].create_matrix(
        VerificationMatrixCreateRequest(
            matrix_key="rc.optional",
            version="0.1.0",
            owner_scope=["workspace:main"],
            required_checks=["tests.brain"],
            optional_checks=["docker_smoke_live"],
            release_ready_threshold=0.95,
        )
    )

    run = services["gate"].run(
        RCGateRunRequest(
            verification_matrix_id=matrix.verification_matrix_id,
            owner_scope=["workspace:main"],
            run_service_checks=False,
            check_results=[_check("tests.brain", "passed")],
        )
    )

    assert run.release_ready is True
    assert run.status == "passed"


def test_rc_collector_accepts_warning_freeze_gate_when_release_ready() -> None:
    collector = VerificationCheckCollector(
        freeze_gate_service=ReadyWarningFreezeGate(),
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )

    checks = collector.collect_service_checks(
        RCGateRunRequest(
            owner_scope=["workspace:main"],
            include_bootstrap=False,
            include_golden_path=False,
            include_release_package=False,
            include_freeze_gate=True,
        )
    )

    freeze_check = next(check for check in checks if check.check_key == "freeze_gate")
    assert freeze_check.status == "passed"


def test_rc_collector_calls_operator_overview_with_request_contract() -> None:
    collector = VerificationCheckCollector(
        operator_service=FakeOperatorService(),
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )

    checks = collector.collect_service_checks(
        RCGateRunRequest(
            owner_scope=["workspace:main"],
            include_bootstrap=False,
            include_golden_path=False,
            include_release_package=False,
            include_freeze_gate=False,
        )
    )

    operator_check = next(check for check in checks if check.check_key == "operator_overview")
    assert operator_check.status == "passed"


def test_rc_resource_registry_check_records_evidence_when_service_absent() -> None:
    collector = VerificationCheckCollector(
        settings=Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:"),
    )

    checks = collector.collect_service_checks(
        RCGateRunRequest(
            owner_scope=["workspace:main"],
            include_bootstrap=False,
            include_golden_path=False,
            include_release_package=False,
            include_freeze_gate=False,
        )
    )

    resource_check = next(check for check in checks if check.check_key == "resource_registry")
    assert resource_check.status == "passed"
    assert resource_check.evidence


def test_rc_policy_denial_blocks_gate() -> None:
    services = _services(DenyPolicy())

    try:
        services["gate"].run(
            RCGateRunRequest(owner_scope=["workspace:main"], run_service_checks=False)
        )
    except Exception as exc:
        assert "denied" in str(exc)
    else:
        raise AssertionError("policy denial did not block RC gate")


def _services(policy: object) -> dict[str, object]:
    settings = Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")
    repository = ReleaseCandidateRepository("sqlite+pysqlite:///:memory:")
    candidate = ReleaseCandidateService(repository, policy)
    matrix = VerificationMatrixService(repository, policy, settings=settings)
    collector = VerificationCheckCollector(settings=settings)
    finding = RCFindingService(repository, policy)
    evidence = RCEvidencePackService(repository, policy)
    report = RCReportService(repository, policy)
    gate = RCGateService(
        repository,
        policy,
        candidate_service=candidate,
        matrix_service=matrix,
        check_collector=collector,
        finding_service=finding,
        evidence_pack_service=evidence,
        report_service=report,
        settings=settings,
    )
    return {
        "repository": repository,
        "matrix": matrix,
        "gate": gate,
    }


def _check(check_key: str, status: str) -> VerificationCheck:
    passed = status == "passed"
    return VerificationCheck(
        verification_check_id=f"check-{check_key.replace('.', '-')}",
        check_key=check_key,
        check_type="unit_tests",
        status=status,
        severity="low" if passed else "critical",
        required=True,
        passed=passed,
        title=check_key,
        summary=f"{check_key} {status}",
        evidence={"source": "test"},
        error={} if passed else {"message": "failed"},
        metadata={},
        created_at=datetime.now(UTC),
    )
