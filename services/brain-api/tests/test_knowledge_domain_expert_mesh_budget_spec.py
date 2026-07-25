from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_domain_expert_mesh_authorization.py"


def _load_validator():
    spec = importlib.util.spec_from_file_location("mesh_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_domain_expert_mesh_resource_limits_are_exact_and_fail_closed():
    validator = _load_validator()
    budget = json.loads(
        (
            REPO_ROOT
            / "examples/knowledge-intelligence/domain-expert-mesh-resource-budget.json"
        ).read_text()
    )
    assert budget["resource_limits"] == validator.RESOURCE_LIMITS
    assert budget["resource_limits"]["maximum_persistent_mesh_write_batch"] == 0
    assert budget["resource_limits"]["maximum_model_provider_calls"] == 0
    assert budget["resource_limits"]["maximum_tool_executions"] == 0
    assert budget["resource_limits"]["maximum_network_calls"] == 0
    assert budget["persistent_mesh_write_allowed"] is False
    assert budget["model_provider_calls_allowed"] is False
    assert budget["tool_executions_allowed"] is False
    assert budget["network_calls_allowed"] is False
