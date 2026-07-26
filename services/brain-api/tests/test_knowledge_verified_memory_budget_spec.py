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


def test_verified_knowledge_resource_limits_are_exact_and_zero_for_runtime_effects() -> None:
    validator = _load_validator()
    auth = _load_json("examples/knowledge-intelligence/verified-knowledge-authorization.json")
    assert auth["resource_limits"] == validator.VERIFIED_KNOWLEDGE_RESOURCE_LIMITS
    for key in (
        "maximum_persistent_verified_knowledge_write_batch",
        "maximum_automatic_knowledge_promotions",
        "maximum_operator_approval_creations",
        "maximum_cognitive_memory_writes",
        "maximum_belief_mutations",
        "maximum_engagement_fact_promotions",
        "maximum_engagement_confidence_effects",
        "maximum_public_network_calls",
        "maximum_actual_tool_executions",
    ):
        assert auth["resource_limits"][key] == 0
