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


def test_tool_verification_resource_limits_are_exact_and_fail_closed() -> None:
    validator = _validator()
    payload = validator.load_json(
        REPO_ROOT,
        "examples/knowledge-intelligence/tool-verification-authorization.json",
    )
    assert payload["resource_limits"] == validator.RESOURCE_LIMITS
    for key in (
        "maximum_persistent_tool_state_write_batch",
        "maximum_actual_tool_executions",
        "maximum_shell_commands",
        "maximum_network_calls",
        "maximum_dns_resolutions",
        "maximum_browser_actions",
        "maximum_connector_calls",
        "maximum_model_provider_calls",
        "maximum_source_mutations",
        "maximum_git_operations",
        "maximum_runtime_created_pull_requests",
        "maximum_approvals_created",
        "maximum_knowledge_promotions",
        "maximum_belief_mutations",
    ):
        assert payload["resource_limits"][key] == 0
