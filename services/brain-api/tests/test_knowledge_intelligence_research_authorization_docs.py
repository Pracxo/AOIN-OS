import json
import os
import subprocess

from knowledge_intelligence_test_helpers import (
    PROGRAM_ID,
    ROOT,
    read_json,
)
from knowledge_source_registry_test_helpers import (
    CLAIM_GRAPH_AUTH_ID,
    CLOSED_AUTH_ID,
    SOURCE_AUTH_ID,
    active_source_record,
    closed_research_record,
    validate_source_authorization,
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
    assert program["program_state"] in {
        "source_provenance_registry_implemented_write_disabled_pending_closeout",
        "temporal_claim_evidence_graph_authorized_not_implemented",
    }
    assert program["active_knowledge_implementation_authorization_count"] == 1
    if program["program_state"] == "temporal_claim_evidence_graph_authorized_not_implemented":
        assert program["active_knowledge_implementation_authorization"] == CLAIM_GRAPH_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-209"
        assert program["formal_closeout_task"] == "AION-210"
    else:
        assert program["active_knowledge_implementation_authorization"] == SOURCE_AUTH_ID
        assert program["active_knowledge_implementation_task"] == "AION-207"
        assert program["formal_closeout_task"] == "AION-208"
    assert program["research_plane_authorized"] is True
    assert program["research_plane_implemented"] is True
    assert program["research_plane_state"] == "implemented_operator_invoked_disabled"
    assert program["research_runtime_enabled"] is False
    assert program["network_access_enabled"] is False
    assert program["knowledge_promotion_enabled"] is False
    assert program["verified_knowledge_memory_enabled"] is False
    assert program["background_crawler_enabled"] is False
    assert program["public_network_fetch_available"] is False
    assert program["source_provenance_registry_implemented"] is True
    assert (
        program["source_provenance_registry_state"]
        == "implemented_append_only_in_memory_replay_persistent_write_disabled"
    )
    assert auth["active_cognitive_implementation_authorization_count"] == 0
    active = [record for record in auth["records"] if record.get("authorization_active") is True]
    assert len(active) == 1
    validate_source_authorization(active_source_record())
    closed = closed_research_record()
    assert closed["authorization_transaction_id"] == CLOSED_AUTH_ID
    assert closed["authorization_active"] is False
    assert closed["authorization_consumed"] is True
    assert closed["authorization_expired"] is True
    assert closed["authorization_reusable"] is False


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
