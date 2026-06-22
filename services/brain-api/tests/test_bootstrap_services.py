"""Bootstrap service tests."""

from __future__ import annotations

from aion_brain.bootstrap.doctor import SetupDoctor
from aion_brain.bootstrap.profiles import BootstrapProfileService
from aion_brain.bootstrap.reports import SetupReportService
from aion_brain.bootstrap.repository import BootstrapRepository
from aion_brain.bootstrap.seed_bundles import SeedBundleService
from aion_brain.bootstrap.seeder import SeedExecutor
from aion_brain.config import Settings
from aion_brain.contracts.bootstrap import SeedExecutionRequest
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.setup_doctor import SetupDoctorRequest


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


def _settings() -> Settings:
    return Settings(_env_file=None, DATABASE_URL="sqlite+pysqlite:///:memory:")


def _services() -> tuple[
    BootstrapRepository,
    BootstrapProfileService,
    SeedBundleService,
    SeedExecutor,
    Settings,
]:
    settings = _settings()
    repository = BootstrapRepository(settings.database_url)
    policy = AllowPolicy()
    profiles = BootstrapProfileService(repository, policy)
    bundles = SeedBundleService(repository, policy)
    executor = SeedExecutor(repository, bundles, policy, settings=settings)
    return repository, profiles, bundles, executor, settings


def test_profile_and_bundle_defaults_seed_idempotent_metadata() -> None:
    repository, profiles, bundles, _executor, _settings_value = _services()
    scope = ["workspace:main"]

    profile_seed = profiles.seed_default_profiles(scope, dry_run=False)
    bundle_seed = bundles.seed_default_bundles(scope, dry_run=False)

    assert profile_seed["dry_run"] is False
    assert bundle_seed["dry_run"] is False
    assert repository.get_profile("local.dev") is not None
    assert repository.get_bundle("core.defaults") is not None


def test_seed_executor_dry_run_skips_without_creating_resources() -> None:
    _repository, _profiles, bundles, executor, _settings_value = _services()
    scope = ["workspace:main"]
    bundles.seed_default_bundles(scope, dry_run=False)

    record = executor.execute(
        SeedExecutionRequest(seed_bundle_key="core.defaults", owner_scope=scope)
    )

    assert record.status == "dry_run"
    assert record.steps_attempted > 0
    assert record.steps_completed == 0
    assert record.steps_skipped > 0
    assert record.result["external_calls"] is False


def test_seed_executor_blocks_controlled_mode_by_default() -> None:
    _repository, _profiles, bundles, executor, _settings_value = _services()
    scope = ["workspace:main"]
    bundles.seed_default_bundles(scope, dry_run=False)

    record = executor.execute(
        SeedExecutionRequest(
            seed_bundle_key="core.defaults",
            owner_scope=scope,
            mode="controlled",
        )
    )

    assert record.status == "blocked_by_policy"
    assert record.result["reason"] == "controlled_seed_disabled"


def test_setup_doctor_and_report_pass_with_local_services() -> None:
    repository, _profiles, _bundles, _executor, settings = _services()
    doctor = SetupDoctor(
        repository,
        AllowPolicy(),
        diagnostics=object(),
        golden_path_repository=None,
        release_smoke=object(),
        operator_service=object(),
        settings=settings,
    )
    result = doctor.run(
        SetupDoctorRequest(
            owner_scope=["workspace:main"],
            include_golden_path=False,
            include_release_smoke=False,
            create_findings=True,
        )
    )
    report_service = SetupReportService(repository, AllowPolicy())
    report = report_service.create_report(result)

    assert result.local_ready is True
    assert result.findings == []
    assert report.local_ready is True
    assert repository.latest_report() is not None
