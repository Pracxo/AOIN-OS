"""Skill autonomy integration tests."""

from tests.autonomy_fakes import FakeAutonomyGovernor
from tests.test_skill_service import (
    FakeSkillRepository,
    make_candidate,
    make_promotion_request,
    make_service,
)


def test_skill_promotion_blocks_when_autonomy_denies_activation() -> None:
    """Skill activation during promotion passes through autonomy."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(status="approved"))
    service = make_service(repository)
    service._autonomy_governor = FakeAutonomyGovernor(allow=False)  # noqa: SLF001

    response = service.promote_candidate(make_promotion_request(activate=True))

    assert response.promoted is False
    assert response.reason == "autonomy_denied:autonomy_denied"
