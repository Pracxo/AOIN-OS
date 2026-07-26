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


def test_verified_knowledge_scope_is_exact_and_creates_only_aion_217_source() -> None:
    validator = _load_validator()
    auth = _load_json("examples/knowledge-intelligence/verified-knowledge-authorization.json")
    assert auth["authorization_transaction_id"] == "AION-216-KI-0007"
    assert auth["candidate_id"] == validator.CANDIDATE_ID
    assert auth["workstream"] == validator.WORKSTREAM
    assert auth["implementation_task"] == "AION-217"
    assert auth["formal_closeout_task"] == "AION-218"
    assert auth["authorization_scope"] == validator.SCOPE
    for relative in validator.AION217_SOURCE_PATHS:
        assert (REPO_ROOT / relative).exists(), relative
    for relative in validator.AION217_OPTIONAL_SOURCE_PATHS:
        assert (REPO_ROOT / relative).exists(), relative
