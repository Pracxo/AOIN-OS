"""Skill Registry API tests."""

from fastapi.testclient import TestClient

from aion_brain.api.dependencies import get_skill_service
from aion_brain.contracts.skills import (
    SkillActivationRequest,
    SkillCandidate,
    SkillMatchRequest,
    SkillMatchResult,
    SkillPromotionRequest,
    SkillPromotionResponse,
    SkillRecord,
)
from aion_brain.main import app
from tests.test_skill_service import make_candidate, make_skill


class FakeSkillService:
    """Skill service fake for API tests."""

    def __init__(self) -> None:
        self.candidate = make_candidate(status="candidate")
        self.skill = make_skill(status="active")

    def create_candidate_from_reflection(self, reflection_id: str) -> SkillCandidate:
        return self.candidate

    def get_candidate(self, candidate_id: str) -> SkillCandidate | None:
        return self.candidate if candidate_id == self.candidate.candidate_id else None

    def list_candidates(
        self,
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillCandidate]:
        return [self.candidate][:limit]

    def update_candidate_status(
        self,
        candidate_id: str,
        status: str,
        reason: str,
    ) -> SkillCandidate:
        self.candidate = self.candidate.model_copy(update={"status": status})
        return self.candidate

    def promote_candidate(self, request: SkillPromotionRequest) -> SkillPromotionResponse:
        return SkillPromotionResponse(
            promoted=True,
            skill_id=self.skill.skill_id,
            skill_version_id="skill-version-1",
            candidate_id=request.candidate_id,
            status="draft",
            reason=None,
        )

    def get_skill(self, skill_id: str, scope: list[str]) -> SkillRecord | None:
        return self.skill if skill_id == self.skill.skill_id else None

    def list_skills(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 50,
    ) -> list[SkillRecord]:
        return [self.skill][:limit]

    def transition_skill(self, request: SkillActivationRequest) -> SkillRecord:
        self.skill = self.skill.model_copy(update={"status": request.to_status})
        return self.skill

    def match_skills(self, request: SkillMatchRequest) -> list[SkillMatchResult]:
        return [
            SkillMatchResult(
                skill=self.skill,
                score=0.8,
                matched_patterns=["question.answer"],
                reason="deterministic_token_overlap",
            )
        ]


def test_skill_api_candidate_status_promotion_and_match_endpoints_work() -> None:
    """Skill endpoints expose candidate, promotion, and matching contracts."""
    service = FakeSkillService()
    app.dependency_overrides[get_skill_service] = lambda: service
    try:
        client = TestClient(app)
        candidate = client.post("/brain/skills/candidates/from-reflection/reflection-1")
        fetched_candidate = client.get("/brain/skills/candidates/candidate-1")
        candidates = client.get("/brain/skills/candidates")
        status = client.post(
            "/brain/skills/candidates/candidate-1/status",
            json={"status": "approved", "reason": "reviewed"},
        )
        promotion = client.post(
            "/brain/skills/promote",
            json={
                "candidate_id": "candidate-1",
                "owner_scope": ["workspace:main"],
                "activate": False,
                "reason": "approved",
            },
        )
        skill = client.get("/brain/skills/skill-1", params={"scope": "workspace:main"})
        skills = client.get("/brain/skills", params={"scope": "workspace:main"})
        transition = client.post(
            "/brain/skills/skill-1/transition",
            json={"to_status": "disabled", "reason": "pause"},
        )
        matches = client.post(
            "/brain/skills/match",
            json={"query": "question plan", "scope": ["workspace:main"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert candidate.status_code == 200
    assert fetched_candidate.status_code == 200
    assert candidates.status_code == 200
    assert status.status_code == 200
    assert status.json()["status"] == "approved"
    assert promotion.status_code == 200
    assert promotion.json()["promoted"] is True
    assert skill.status_code == 200
    assert skills.status_code == 200
    assert transition.status_code == 200
    assert transition.json()["status"] == "disabled"
    assert matches.status_code == 200
    assert matches.json()[0]["skill"]["skill_id"] == "skill-1"
