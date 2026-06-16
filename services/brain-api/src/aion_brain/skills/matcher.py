"""Deterministic active skill matcher."""

import re

from aion_brain.contracts.skills import SkillMatchRequest, SkillMatchResult, SkillRecord

TOKEN_PATTERN = r"[a-z0-9_.]+"


class SkillMatcher:
    """Matches active procedural skills without executing them."""

    def __init__(self, repository: object) -> None:
        self._repository = repository

    def match(self, request: SkillMatchRequest) -> list[SkillMatchResult]:
        """Return active skills ranked by deterministic token overlap."""
        list_skills = getattr(self._repository, "list_skills", None)
        if not callable(list_skills):
            return []
        skills = list_skills(scope=request.scope, status="active", limit=max(50, request.limit))
        if not isinstance(skills, list):
            return []
        results = [
            _score_skill(skill, request)
            for skill in skills
            if isinstance(skill, SkillRecord)
            and (not request.risk_levels or skill.risk_level in request.risk_levels)
        ]
        return sorted(
            [result for result in results if result.score > 0.0],
            key=lambda result: (-result.score, result.skill.skill_id),
        )[: request.limit]


def _score_skill(skill: SkillRecord, request: SkillMatchRequest) -> SkillMatchResult:
    query_tokens = _tokens(request.query)
    pattern_scores = [
        (_overlap(query_tokens, _tokens(pattern)), pattern) for pattern in skill.trigger_patterns
    ]
    trigger_overlap = max((score for score, _ in pattern_scores), default=0.0)
    matched_patterns = [pattern for score, pattern in pattern_scores if score > 0.0]
    description_overlap = _overlap(query_tokens, _tokens(f"{skill.name} {skill.description}"))
    risk_match = 1.0 if not request.risk_levels or skill.risk_level in request.risk_levels else 0.0
    score = max(
        0.0,
        min(
            1.0,
            0.55 * trigger_overlap + 0.25 * description_overlap + 0.20 * risk_match,
        ),
    )
    return SkillMatchResult(
        skill=skill,
        score=round(score, 4),
        matched_patterns=matched_patterns,
        reason="deterministic_token_overlap",
    )


def _tokens(value: str) -> set[str]:
    return set(re.findall(TOKEN_PATTERN, value.lower()))


def _overlap(query_tokens: set[str], candidate_tokens: set[str]) -> float:
    if not query_tokens or not candidate_tokens:
        return 0.0
    return len(query_tokens & candidate_tokens) / len(query_tokens)
