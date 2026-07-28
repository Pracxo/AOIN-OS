from __future__ import annotations

from test_governed_learning_memory_program_authorization import REPO_ROOT, load_json


def test_required_local_persistence_docs_examples_and_static_payloads_exist() -> None:
    docs = [
        "local-persistence-architecture.md",
        "local-persistence-boundary.md",
        "local-persistence-authorization-model.md",
        "local-persistence-approval-policy.md",
        "local-persistence-content-envelope.md",
        "local-persistence-sqlite-policy.md",
        "local-persistence-schema.md",
        "local-persistence-append-only-semantics.md",
        "local-persistence-hash-chain.md",
        "local-persistence-memory-projection.md",
        "local-persistence-belief-candidate-boundary.md",
        "local-persistence-backup-restore.md",
        "local-persistence-resource-budgets.md",
        "local-persistence-integrity.md",
        "local-persistence-threat-model.md",
        "local-persistence-roadmap.md",
    ]
    for name in docs:
        assert (REPO_ROOT / "docs/governed-learning-memory" / name).is_file(), name
    release = [
        "governed-learning-memory-local-persistence-authorization-transaction.md",
        "governed-learning-memory-local-persistence-explicit-approval-record.md",
        "governed-learning-memory-local-persistence-scope.md",
        "governed-learning-memory-local-persistence-runtime-hold.md",
        "governed-learning-memory-local-persistence-no-go.md",
        "governed-learning-memory-local-persistence-checklist.md",
        "governed-learning-memory-local-persistence-evidence-matrix.md",
    ]
    for name in release:
        assert (REPO_ROOT / "docs/release" / name).is_file(), name
    for rel in [
        "examples/governed-learning-memory/local-persistence-authorization.json",
        "examples/governed-learning-memory/local-persistence-authorization-envelope.json",
        "examples/governed-learning-memory/local-persistence-approval-evidence.json",
        "operator-console-static/demo-data/governed-learning-memory-local-persistence-runtime-hold.json",
    ]:
        assert load_json(rel), rel
