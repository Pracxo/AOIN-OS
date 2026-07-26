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


def test_verified_knowledge_threat_model_and_runtime_hold_keep_boundaries_false() -> None:
    doc = (REPO_ROOT / "docs/knowledge-intelligence/verified-knowledge-threat-model.md").read_text(
        encoding="utf-8"
    )
    for marker in (
        "Evidence laundering",
        "duplicate amplification",
        "confidence amplification",
        "tool-output-as-fact",
        "engagement-as-fact",
        "automatic promotion",
        "public-network activation",
        "evaluation-as-approval",
    ):
        assert marker in doc
    runtime = _load_json("examples/knowledge-intelligence/verified-knowledge-runtime-hold.json")
    for key in (
        "verified_knowledge_runtime_enabled",
        "verified_knowledge_database_enabled",
        "automatic_verified_knowledge_promotion_enabled",
        "cognitive_memory_write_enabled",
        "belief_mutation_enabled",
        "engagement_signal_as_fact_enabled",
        "engagement_confidence_effect_enabled",
        "public_network_fetch_enabled",
        "actual_tool_execution_enabled",
    ):
        assert runtime[key] is False
