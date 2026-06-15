"""Skill matcher tests."""

from aion_brain.contracts.skills import SkillMatchRequest
from aion_brain.skills.matcher import SkillMatcher
from tests.test_skill_service import FakeSkillRepository, make_skill


def test_skill_matcher_returns_active_skill_matches() -> None:
    """Active skills can be matched as procedural memory."""
    repository = FakeSkillRepository()
    repository.save_skill(make_skill(status="active"))

    results = SkillMatcher(repository).match(
        SkillMatchRequest(query="question plan create", scope=["workspace:main"])
    )

    assert results[0].skill.skill_id == "skill-1"
    assert results[0].score > 0.0


def test_skill_matcher_excludes_draft_skills_by_default() -> None:
    """Draft skills do not appear in active matches."""
    repository = FakeSkillRepository()
    repository.save_skill(make_skill(status="draft"))

    results = SkillMatcher(repository).match(
        SkillMatchRequest(query="question plan create", scope=["workspace:main"])
    )

    assert results == []
