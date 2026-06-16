"""Run-level service tests."""

from datetime import UTC, datetime, timedelta

from aion_brain.autonomy.run_level import RunLevelService
from aion_brain.contracts.autonomy import SetRunLevelRequest
from tests.autonomy_fakes import AllowPolicy, autonomy_repository


def test_run_level_service_sets_and_replaces_active_level() -> None:
    """Setting a run level ends the previous active override."""
    repository = autonomy_repository()
    service = RunLevelService(repository, AllowPolicy())

    first = service.set_run_level(SetRunLevelRequest(run_level="observe", reason="observe only"))
    second = service.set_run_level(SetRunLevelRequest(run_level="dry_run", reason="enable dry run"))

    assert repository.get_run_level(first.run_level_id).status == "ended"
    assert service.get_active_run_level(None, None) == second


def test_run_level_service_expires_old_records() -> None:
    """Expired run levels are marked expired deterministically."""
    service = RunLevelService(autonomy_repository(), AllowPolicy())
    service.set_run_level(
        SetRunLevelRequest(
            run_level="observe",
            reason="temporary override",
            expires_at=datetime.now(UTC) - timedelta(seconds=1),
        )
    )

    expired = service.expire_old_run_levels(datetime.now(UTC))

    assert len(expired) == 1
    assert expired[0].status == "expired"


def test_run_level_service_policy_deny_blocks_set() -> None:
    """Run-level changes must pass the policy boundary."""
    service = RunLevelService(
        autonomy_repository(),
        AllowPolicy(deny_action="autonomy.run_level.set"),
    )

    try:
        service.set_run_level(SetRunLevelRequest(run_level="observe", reason="blocked"))
    except PermissionError as exc:
        assert str(exc) == "denied"
    else:
        raise AssertionError("expected PermissionError")
