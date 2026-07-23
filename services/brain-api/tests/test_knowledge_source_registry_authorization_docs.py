import json
import os
import subprocess

from knowledge_source_registry_test_helpers import (
    DECISION,
    RESOURCE_LIMITS,
    ROOT,
    SOURCE_AUTH_ID,
    SOURCE_SCOPE,
    active_source_record,
    read_json,
    validate_source_authorization,
)

REQUIRED_FILES = [
    "docs/knowledge-intelligence/source-provenance-registry-architecture.md",
    "docs/knowledge-intelligence/source-provenance-registry-boundary.md",
    "docs/knowledge-intelligence/source-provenance-registry-data-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-persistence.md",
    "docs/knowledge-intelligence/source-provenance-registry-resource-budgets.md",
    "docs/knowledge-intelligence/source-provenance-registry-threat-model.md",
    "docs/knowledge-intelligence/source-provenance-registry-roadmap.md",
    "docs/release/knowledge-intelligence-source-registry-authorization-transaction.md",
    "docs/release/knowledge-intelligence-source-registry-explicit-approval-record.md",
    "docs/release/knowledge-intelligence-source-registry-scope.md",
    "docs/release/knowledge-intelligence-source-registry-runtime-hold.md",
    "docs/release/knowledge-intelligence-source-registry-no-go.md",
    "docs/release/knowledge-intelligence-source-registry-checklist.md",
    "docs/release/knowledge-intelligence-source-registry-evidence-matrix.md",
    "examples/knowledge-intelligence/source-registry-authorization.json",
    "examples/knowledge-intelligence/source-registry-record-envelope.json",
    "examples/knowledge-intelligence/source-registry-resource-budget.json",
    "examples/knowledge-intelligence/source-registry-runtime-hold.json",
    "examples/knowledge-intelligence/source-registry-operator-review-item.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-authorization.json",
    "operator-console-static/demo-data/knowledge-intelligence-source-registry-runtime-hold.json",
    "scripts/knowledge-intelligence-source-registry-authorization-check.sh",
    "scripts/knowledge-intelligence-source-registry-authorization-no-go-regression.sh",
    "scripts/knowledge-intelligence-source-registry-runtime-hold.sh",
]


def test_source_registry_required_files_and_examples():
    for relative in REQUIRED_FILES:
        path = ROOT / relative
        assert path.is_file(), relative
        if relative.startswith("scripts/"):
            assert os.access(path, os.X_OK), relative
    payload = read_json("examples/knowledge-intelligence/source-registry-authorization.json")
    assert payload["authorization_transaction_id"] == SOURCE_AUTH_ID
    assert payload["authorization_scope"] == SOURCE_SCOPE
    assert payload["resource_limits"] == RESOURCE_LIMITS
    assert payload["source_provenance_registry_implemented"] is False
    assert payload["source_body_persistence_enabled"] is False
    assert payload["claim_verification_enabled"] is False
    assert payload["knowledge_promotion_enabled"] is False
    assert payload["belief_mutation_enabled"] is False
    assert payload["network_access_enabled"] is False
    rendered = json.dumps(payload, sort_keys=True).lower()
    assert '"source_body_persistence_enabled": true' not in rendered
    assert '"network_access_enabled": true' not in rendered


def test_source_registry_authorization_record_validates_and_script_passes():
    validate_source_authorization(active_source_record())
    env = {**os.environ, "PYTEST_CURRENT_TEST": "AION-206 source registry smoke"}
    subprocess.run(
        [str(ROOT / "scripts/knowledge-intelligence-source-registry-authorization-check.sh")],
        cwd=ROOT,
        env=env,
        check=True,
    )
    report = read_json(
        "examples/knowledge-intelligence/research-acquisition-operator-evaluation-report.json"
    )
    assert (
        report["conditional_next_authorization"]["authorization_transaction_id"] == SOURCE_AUTH_ID
    )
    assert report["decision"] == DECISION
