"""Skill repository tests."""

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.skills.repository import SkillRepository
from tests.test_skill_service import make_candidate, make_skill, make_version


def test_skill_repository_persists_candidates_skills_and_versions() -> None:
    """SkillRepository stores Brain-owned skill registry contracts."""
    repository = SkillRepository(engine=sqlite_engine())
    candidate = repository.save_candidate(make_candidate())
    skill = repository.save_skill(make_skill(candidate_id=candidate.candidate_id))
    version = repository.save_version(make_version(skill.skill_id, candidate.candidate_id))

    assert repository.get_candidate(candidate.candidate_id) == candidate
    assert repository.list_candidates(status="candidate")[0].candidate_id == candidate.candidate_id
    assert repository.get_skill(skill.skill_id) == skill
    listed_skill = repository.list_skills(scope=["workspace:main"], status="active")[0]
    assert listed_skill.skill_id == skill.skill_id
    assert version.skill_id == skill.skill_id


def sqlite_engine() -> object:
    """Create an in-memory SQLite engine."""
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
