from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_tool_verification_authorization.py"


def _validator():
    spec = importlib.util.spec_from_file_location("tool_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_tool_verification_scope_is_exact_for_aion_215() -> None:
    validator = _validator()
    payload = validator.load_json(
        REPO_ROOT,
        "examples/knowledge-intelligence/tool-verification-authorization.json",
    )
    assert payload["authorization_transaction_id"] == "AION-214-KI-0006"
    assert payload["implementation_task"] == "AION-215"
    assert payload["formal_closeout_task"] == "AION-216"
    assert payload["authorization_scope"] == validator.SCOPE
    assert tuple(payload["future_aion215_create_paths"]) == validator.AION215_SOURCE_FILES
    assert tuple(payload["future_aion215_update_paths"]) == validator.AION215_UPDATE_FILES
