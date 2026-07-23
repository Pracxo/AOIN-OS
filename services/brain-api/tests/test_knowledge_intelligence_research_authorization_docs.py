import json
import os
import subprocess

from knowledge_intelligence_test_helpers import (
    AUTH_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ROOT,
    read_json,
    validate_authorization_record,
)

REQUIRED_FILES = [
    "docs/cognitive-architecture/aion-203-postmerge-verification.md",
    "docs/knowledge-intelligence/program-charter.md",
    "docs/knowledge-intelligence/architecture-roadmap.md",
    "docs/knowledge-intelligence/security-boundary.md",
    "docs/knowledge-intelligence/operator-model.md",
    "docs/knowledge-intelligence/non-destructive-evolution.md",
    "docs/knowledge-intelligence/research-source-policy.md",
    "docs/knowledge-intelligence/research-data-governance.md",
    "docs/knowledge-intelligence/research-resource-budgets.md",
    "docs/knowledge-intelligence/research-threat-model.md",
    "docs/knowledge-intelligence/research-runtime-hold.md",
    "docs/knowledge-intelligence/program-ledger.json",
    "docs/knowledge-intelligence/authorization-ledger.json",
    "examples/knowledge-intelligence/research-authorization.json",
    "examples/knowledge-intelligence/research-plan-boundary.json",
    "examples/knowledge-intelligence/research-resource-budget.json",
    "examples/knowledge-intelligence/research-source-policy.json",
    "examples/knowledge-intelligence/research-runtime-hold.json",
    "examples/knowledge-intelligence/research-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-program.json",
    "operator-console-static/demo-data/knowledge-intelligence-research-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-research-runtime-hold.json",
    "scripts/knowledge-intelligence-research-authorization-check.sh",
    "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-research-runtime-hold.sh",
]


def test_required_files_exist_and_scripts_executable():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative


def test_ledgers_create_single_active_knowledge_authorization():
    program = read_json("docs/knowledge-intelligence/program-ledger.json")
    auth = read_json("docs/knowledge-intelligence/authorization-ledger.json")
    assert program["program_id"] == PROGRAM_ID
    assert program["program_state"] == "research_plane_implemented_disabled_pending_closeout"
    assert program["active_knowledge_implementation_authorization_count"] == 1
    assert program["active_knowledge_implementation_authorization"] == AUTH_ID
    assert program["active_knowledge_implementation_task"] == IMPLEMENTATION_TASK
    assert program["formal_closeout_task"] == FORMAL_CLOSEOUT_TASK
    assert program["research_plane_authorized"] is True
    assert program["research_plane_implemented"] is True
    assert program["research_plane_state"] == "implemented_operator_invoked_disabled"
    assert program["research_runtime_enabled"] is False
    assert program["network_access_enabled"] is False
    assert program["knowledge_promotion_enabled"] is False
    assert program["verified_knowledge_memory_enabled"] is False
    assert program["background_crawler_enabled"] is False
    assert program["public_network_fetch_available"] is False
    assert auth["active_cognitive_implementation_authorization_count"] == 0
    active = [record for record in auth["records"] if record.get("authorization_active") is True]
    assert len(active) == 1
    validate_authorization_record(active[0])


def test_json_examples_have_required_metadata_and_no_secret_patterns():
    for relative in [path for path in REQUIRED_FILES if path.endswith(".json")]:
        payload = read_json(relative)
        assert payload["synthetic"] is True
        assert payload["read_only"] is True
        assert payload["redacted"] is True
        rendered = json.dumps(payload, sort_keys=True)
        for forbidden in ("sk-", "ghp_", "gho_", "xoxb-", "raw user message"):
            assert forbidden not in rendered


def test_scripts_pass_in_nested_mode():
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-204 focused script smoke"}
    for script in (
        "scripts/knowledge-intelligence-research-authorization-no-go-regression.sh",
        "scripts/knowledge-intelligence-research-authorization-check.sh",
    ):
        subprocess.run([str(ROOT / script)], cwd=ROOT, env=env, check=True)
