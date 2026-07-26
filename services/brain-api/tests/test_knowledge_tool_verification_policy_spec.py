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


def test_tool_verification_policy_authorizes_simulation_not_execution() -> None:
    validator = _validator()
    payload = validator.load_json(
        REPO_ROOT,
        "examples/knowledge-intelligence/tool-verification-authorization.json",
    )
    assert payload["authorized_capabilities"] == validator.expected_authorized_capabilities()
    assert payload["prohibited_capabilities"] == validator.expected_prohibited_capabilities()
    assert payload["actual_tool_execution_enabled"] is False
    assert payload["tool_output_as_verified_fact_enabled"] is False
    assert payload["tool_result_as_automatic_knowledge_enabled"] is False
    assert payload["approval_creation_enabled"] is False
    assert payload["runtime_effect"] is False
