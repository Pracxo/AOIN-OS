from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_verified_knowledge_candidate_policy_blocks_unsafe_inputs() -> None:
    candidate = _load_json("examples/knowledge-intelligence/verified-knowledge-candidate.json")
    assert candidate["candidate_kind"] == "support_candidate"
    assert candidate["eligibility_status"] == "eligible_for_operator_review"
    assert candidate["assessment_confidence"] == "0.910000"
    assert candidate["independent_support_count"] == 3
    assert candidate["citation_coverage"] == "1.000000"
    assert candidate["provenance_completeness"] == "1.000000"
    assert candidate["operator_review_required"] is True
    assert candidate["automatic_promotion"] is False
    assert {
        item["candidate_kind"]
        for item in _load_json(
            "examples/knowledge-intelligence/verified-knowledge-candidate-batch.json"
        )["candidates"]
    } == {"support_candidate", "refutation_candidate"}
    statuses = _load_validator().ELIGIBILITY_STATUSES
    assert (
        "ineligible_low_confidence" in statuses
        and "ineligible_unresolved_contradiction" in statuses
        and "ineligible_material_dissent" in statuses
    )
