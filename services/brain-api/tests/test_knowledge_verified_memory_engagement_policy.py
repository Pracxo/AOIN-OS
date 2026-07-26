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


def test_engagement_signal_policy_is_non_factual() -> None:
    validator = _load_validator()
    signal = _load_json("examples/knowledge-intelligence/engagement-signal-metadata.json")
    learning = _load_json("examples/knowledge-intelligence/engagement-learning-candidate.json")
    assert tuple(signal["allowed_signal_kinds"]) == validator.ENGAGEMENT_SIGNAL_KINDS
    assert (
        signal["factual_effect"] is False
        and signal["confidence_effect"] is False
        and signal["knowledge_effect"] is False
        and signal["belief_effect"] is False
    )
    assert (
        tuple(learning["allowed_learning_candidate_kinds"])
        == validator.ENGAGEMENT_LEARNING_CANDIDATE_KINDS
    )
    assert learning["automatic_policy_application"] is False and learning["model_training"] is False
