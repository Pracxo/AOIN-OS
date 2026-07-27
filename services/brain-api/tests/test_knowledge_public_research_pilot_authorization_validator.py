from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PUBLIC_AUTH_VALIDATOR = (
    REPO_ROOT / "scripts/lib/knowledge_intelligence_public_research_pilot_authorization.py"
)


def load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def load_public_auth():
    spec = importlib.util.spec_from_file_location("public_auth", PUBLIC_AUTH_VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def public_auth() -> dict[str, object]:
    return load_json("examples/knowledge-intelligence/public-research-pilot-authorization.json")


def test_public_research_pilot_authorization_validator_passes() -> None:
    validator = load_public_auth()
    validator.validate_authorization_files(REPO_ROOT)
    validator.validate_runtime_hold(REPO_ROOT)


def test_public_research_pilot_authorization_exact_fields() -> None:
    auth = public_auth()
    assert auth["authorization_transaction_id"] == "AION-218-KI-0008"
    assert auth["approval_record_id"] == "AION-218-KI-0008"
    assert auth["parent_evaluation_id"] == "AION-VKME-001"
    assert auth["implementation_task"] == "AION-219"
    assert auth["formal_closeout_task"] == "AION-220"
    assert auth["authorization_active"] is False
    assert auth["authorization_consumed"] is True
    assert auth["authorization_expired"] is True
    assert auth["authorization_reusable"] is False
    assert auth["authorization_closed_by_task"] == "AION-220"
    assert auth["authorization_consumed_by_task"] == "AION-219"
