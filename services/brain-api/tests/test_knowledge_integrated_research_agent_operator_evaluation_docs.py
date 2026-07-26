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


def test_integrated_research_agent_docs_and_examples_exist() -> None:
    for relative in (
        "docs/knowledge-intelligence/integrated-research-agent-operator-evaluation-closeout.md",
        "docs/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.md",
        "docs/knowledge-intelligence/integrated-research-agent-evaluation-scenarios.md",
        "docs/knowledge-intelligence/integrated-research-agent-lineage.md",
        "docs/knowledge-intelligence/integrated-research-agent-security-boundary.md",
        "docs/release/knowledge-intelligence-integrated-research-agent-evaluation-closeout.md",
        "docs/release/knowledge-intelligence-integrated-research-agent-evaluation-checklist.md",
        "docs/release/knowledge-intelligence-integrated-research-agent-evaluation-evidence-matrix.md",
        "docs/release/knowledge-intelligence-integrated-research-agent-evaluation-runtime-hold.md",
        "examples/knowledge-intelligence/integrated-research-agent-operator-evaluation-report.json",
        "examples/knowledge-intelligence/integrated-research-agent-evaluation-scenario-summary.json",
        "examples/knowledge-intelligence/integrated-knowledge-lineage.json",
        "docs/adr/0180-integrated-research-agent-evaluation-and-verified-knowledge-memory-authorization.md",
    ):
        assert (REPO_ROOT / relative).is_file(), relative


def test_integrated_report_validates_and_is_indexed() -> None:
    report = _load_validator().validate_report(REPO_ROOT)
    assert report["evaluation_id"] == "AION-IRAE-001"
    assert report["scenario_count"] == 28
    assert (
        "0180-integrated-research-agent-evaluation-and-verified-knowledge-memory-authorization.md"
        in (REPO_ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    )
