from __future__ import annotations

from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


def test_required_governed_learning_memory_documents_exist() -> None:
    required = [
        "docs/governed-learning-memory/program-charter.md",
        "docs/governed-learning-memory/architecture-roadmap.md",
        "docs/governed-learning-memory/security-boundary.md",
        "docs/governed-learning-memory/operator-model.md",
        "docs/governed-learning-memory/program-ledger.json",
        "docs/governed-learning-memory/authorization-ledger.json",
        "docs/governed-learning-memory/knowledge-promotion-transaction-architecture.md",
        "docs/governed-learning-memory/knowledge-memory-bridge-boundary.md",
        "docs/governed-learning-memory/approval-and-separation-of-duties.md",
        "docs/governed-learning-memory/knowledge-identity-and-versioning.md",
        "docs/governed-learning-memory/conflict-supersession-retraction-policy.md",
        "docs/governed-learning-memory/memory-projection-policy.md",
        "docs/governed-learning-memory/rollback-and-compensation-policy.md",
        "docs/governed-learning-memory/resource-budgets.md",
        "docs/governed-learning-memory/threat-model.md",
        "docs/governed-learning-memory/aion-221-checklist.md",
        "docs/release/governed-learning-memory-program-authorization.md",
        "docs/release/governed-learning-memory-explicit-approval-record.md",
        "docs/release/governed-learning-memory-scope.md",
        "docs/release/governed-learning-memory-runtime-hold.md",
        "docs/release/governed-learning-memory-no-go.md",
        "docs/release/governed-learning-memory-checklist.md",
        "docs/release/governed-learning-memory-evidence-matrix.md",
        "docs/adr/0185-governed-learning-and-memory-integration-program-charter.md",
    ]
    for relative in required:
        assert (REPO_ROOT / relative).is_file(), relative


def test_required_examples_and_static_console_payloads_exist() -> None:
    required = [
        "examples/governed-learning-memory/program-authorization.json",
        "examples/governed-learning-memory/program-roadmap.json",
        "examples/governed-learning-memory/knowledge-promotion-request.json",
        "examples/governed-learning-memory/operator-approval-evidence.json",
        "examples/governed-learning-memory/promotion-eligibility-snapshot.json",
        "examples/governed-learning-memory/knowledge-identity-plan.json",
        "examples/governed-learning-memory/knowledge-version-plan.json",
        "examples/governed-learning-memory/cognitive-memory-projection-plan.json",
        "examples/governed-learning-memory/promotion-transaction-plan.json",
        "examples/governed-learning-memory/rollback-plan.json",
        "examples/governed-learning-memory/runtime-hold.json",
        "operator-console-static/demo-data/governed-learning-memory-program.json",
        "operator-console-static/demo-data/governed-learning-memory-authorization.json",
        "operator-console-static/demo-data/governed-learning-memory-roadmap.json",
        "operator-console-static/demo-data/governed-learning-memory-boundary.json",
        "operator-console-static/demo-data/governed-learning-memory-runtime-hold.json",
    ]
    for relative in required:
        assert load_json(relative), relative


def test_adr_0185_is_indexed() -> None:
    adr_index = (REPO_ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    assert "0185-governed-learning-and-memory-integration-program-charter.md" in adr_index
