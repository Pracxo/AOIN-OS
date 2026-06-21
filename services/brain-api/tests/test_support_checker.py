from __future__ import annotations

from aion_brain.contracts.grounding import GroundingSource
from aion_brain.grounding.support_checker import SupportChecker
from tests.grounding_helpers import source


def test_support_checker_supports_exact_match() -> None:
    result = SupportChecker().check_statement(
        "AION records deterministic source support.",
        [source()],
        require_evidence=False,
        allow_memory_only=False,
    )

    assert result["supported"] is True
    assert result["support_level"] == "strong"


def test_support_checker_treats_memory_only_as_weak_when_disallowed() -> None:
    memory_source = GroundingSource(
        **{
            **source().model_dump(),
            "grounding_source_id": "memory-source-1",
            "source_type": "memory",
            "source_id": "memory-1",
            "trust_level": "memory_recall",
            "memory_refs": ["memory-1"],
            "evidence_refs": [],
        }
    )

    result = SupportChecker().check_statement(
        "AION records deterministic source support.",
        [memory_source],
        require_evidence=False,
        allow_memory_only=False,
    )

    assert result["supported"] is False
    assert "memory_not_truth" in result["issues"]


def test_support_checker_flags_contradicted_belief() -> None:
    contradicted = GroundingSource(
        **{
            **source().model_dump(),
            "source_type": "belief_claim",
            "source_id": "claim-1",
            "trust_level": "unverified",
            "metadata": {"belief_status": "contradicted"},
        }
    )

    result = SupportChecker().check_statement(
        "AION records deterministic source support.",
        [contradicted],
        require_evidence=False,
        allow_memory_only=True,
    )

    assert result["supported"] is False
    assert "contradicted_support" in result["issues"]
