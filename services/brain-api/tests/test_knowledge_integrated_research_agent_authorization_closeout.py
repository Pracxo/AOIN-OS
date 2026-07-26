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


def test_aion_214_closeout_and_aion_216_authorization_are_exact() -> None:
    report = _load_json(
        "examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json"
    )
    closeout = report["authorization_closeout"]
    assert closeout["authorization_transaction_id"] == "AION-214-KI-0006"
    assert closeout["authorization_active"] is False
    assert closeout["authorization_consumed"] is True
    assert closeout["authorization_expired"] is True
    assert closeout["authorization_reusable"] is False
    assert closeout["authorization_consumed_by_task"] == "AION-215"
    assert closeout["authorization_consumed_by_prs"] == [129]
    auth = report["conditional_next_authorization"]
    assert auth["authorization_transaction_id"] == "AION-216-KI-0007"
    assert auth["implementation_task"] == "AION-217"
    assert auth["formal_closeout_task"] == "AION-218"
    assert auth["authorization_scope"] == _load_validator().SCOPE
    assert auth["authorization_active"] is True
    assert auth["authorization_consumed"] is False
    assert auth["authorization_expired"] is False
    assert auth["authorization_reusable"] is False
