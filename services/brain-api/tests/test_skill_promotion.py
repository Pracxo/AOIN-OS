"""Skill promotion gate tests."""

from aion_brain.skills.service import SkillService
from tests.test_skill_service import (
    FakePolicyAdapter,
    FakeSkillRepository,
    make_candidate,
    make_promotion_request,
    make_service,
)


def test_promotion_requires_policy_allow() -> None:
    """Policy denial prevents skill promotion."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(status="approved"))
    service = make_service(
        repository,
        policy=FakePolicyAdapter(deny_actions={"skill.promote"}),
    )

    response = service.promote_candidate(make_promotion_request())

    assert response.promoted is False
    assert response.reason == "policy_denied:denied"


def test_promotion_service_keeps_skills_as_registry_records() -> None:
    """Promotion is handled by SkillService, not executable code generation."""
    repository = FakeSkillRepository()
    repository.save_candidate(make_candidate(status="approved"))

    response = make_service(repository).promote_candidate(make_promotion_request())

    assert response.promoted is True
    assert response.skill_id in repository.skills
    assert isinstance(make_service(repository), SkillService)
