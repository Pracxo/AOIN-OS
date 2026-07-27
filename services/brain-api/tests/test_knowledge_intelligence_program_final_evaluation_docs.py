from __future__ import annotations

import json
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FINAL_REPORT = (
    REPO_ROOT
    / "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json"
)


def _require_final_closeout() -> None:
    if not FINAL_REPORT.exists():
        pytest.skip("AION-220 final closeout evidence is not committed yet")


def test_final_program_docs_and_adr_are_present() -> None:
    _require_final_closeout()
    required = [
        "docs/knowledge-intelligence/program-final-evaluation-closeout.md",
        "docs/knowledge-intelligence/program-final-evaluation-report.md",
        "docs/knowledge-intelligence/program-final-evaluation-scenarios.md",
        "docs/knowledge-intelligence/program-final-capability-matrix.md",
        "docs/knowledge-intelligence/program-final-security-boundary.md",
        "docs/knowledge-intelligence/program-final-runtime-boundary.md",
        "docs/knowledge-intelligence/program-final-operator-runbook.md",
        "docs/knowledge-intelligence/program-final-roadmap.md",
        "docs/release/knowledge-intelligence-program-final-closeout.md",
        "docs/release/knowledge-intelligence-program-final-checklist.md",
        "docs/release/knowledge-intelligence-program-final-evidence-matrix.md",
        "docs/release/knowledge-intelligence-program-final-runtime-hold.md",
        "docs/release/knowledge-intelligence-program-final-no-go.md",
        "docs/adr/0184-final-knowledge-intelligence-program-evaluation-and-closeout.md",
    ]
    for relative in required:
        assert (REPO_ROOT / relative).is_file(), relative
    adr_index = (REPO_ROOT / "docs/adr/README.md").read_text(encoding="utf-8")
    assert "0184-final-knowledge-intelligence-program-evaluation-and-closeout.md" in adr_index


def test_final_program_examples_and_static_console_evidence_are_present() -> None:
    _require_final_closeout()
    required_json = [
        "examples/knowledge-intelligence/knowledge-intelligence-program-final-evaluation-report.json",
        "examples/knowledge-intelligence/knowledge-intelligence-program-final-scenario-summary.json",
        "examples/knowledge-intelligence/knowledge-intelligence-program-final-capability-matrix.json",
        "examples/knowledge-intelligence/knowledge-intelligence-program-final-runtime-state.json",
        "examples/knowledge-intelligence/knowledge-intelligence-program-final-authorization-closeout.json",
        "operator-console-static/demo-data/knowledge-intelligence-program-final-evaluation.json",
        "operator-console-static/demo-data/knowledge-intelligence-program-final-capabilities.json",
        "operator-console-static/demo-data/knowledge-intelligence-program-final-runtime-boundary.json",
        "operator-console-static/demo-data/knowledge-intelligence-program-complete.json",
    ]
    for relative in required_json:
        payload = json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))
        assert payload
