from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
VALIDATOR = REPO_ROOT / "scripts/lib/knowledge_intelligence_verified_knowledge_authorization.py"
HARNESS = (
    REPO_ROOT
    / "scripts/lib/knowledge_intelligence_integrated_research_agent_operator_evaluation.py"
)


def _load_validator():
    sys.path.insert(0, str(REPO_ROOT / "scripts/lib"))
    spec = importlib.util.spec_from_file_location("verified_auth", VALIDATOR)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_json(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_verified_knowledge_docs_examples_and_release_evidence_exist() -> None:
    for relative in (
        "docs/knowledge-intelligence/verified-knowledge-memory-architecture.md",
        "docs/knowledge-intelligence/verified-knowledge-memory-boundary.md",
        "docs/knowledge-intelligence/verified-knowledge-candidate-model.md",
        "docs/knowledge-intelligence/verified-knowledge-eligibility-policy.md",
        "docs/knowledge-intelligence/verified-knowledge-lineage-model.md",
        "docs/knowledge-intelligence/verified-knowledge-versioning.md",
        "docs/knowledge-intelligence/verified-knowledge-revalidation.md",
        "docs/knowledge-intelligence/verified-knowledge-abstention.md",
        "docs/knowledge-intelligence/verified-knowledge-operator-review.md",
        "docs/knowledge-intelligence/engagement-signal-policy.md",
        "docs/knowledge-intelligence/engagement-learning-candidate-model.md",
        "docs/knowledge-intelligence/engagement-learning-boundary.md",
        "docs/knowledge-intelligence/verified-knowledge-resource-budgets.md",
        "docs/knowledge-intelligence/verified-knowledge-threat-model.md",
        "docs/knowledge-intelligence/verified-knowledge-roadmap.md",
        "docs/release/knowledge-intelligence-verified-knowledge-authorization-transaction.md",
        "docs/release/knowledge-intelligence-verified-knowledge-explicit-approval-record.md",
        "docs/release/knowledge-intelligence-verified-knowledge-scope.md",
        "docs/release/knowledge-intelligence-verified-knowledge-runtime-hold.md",
        "docs/release/knowledge-intelligence-verified-knowledge-no-go.md",
        "docs/release/knowledge-intelligence-verified-knowledge-checklist.md",
        "docs/release/knowledge-intelligence-verified-knowledge-evidence-matrix.md",
    ):
        assert (REPO_ROOT / relative).is_file(), relative
