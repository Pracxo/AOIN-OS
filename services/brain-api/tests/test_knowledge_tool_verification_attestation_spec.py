from __future__ import annotations

import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]


def _load(relative: str) -> dict[str, object]:
    return json.loads((REPO_ROOT / relative).read_text(encoding="utf-8"))


def test_tool_verification_session_preserves_independent_attestation_boundary() -> None:
    session = _load("examples/knowledge-intelligence/tool-verification-session.json")
    attestation = _load("examples/knowledge-intelligence/tool-attestation.json")
    finding = _load("examples/knowledge-intelligence/tool-verification-finding.json")

    assert session["overall_status"] == "simulation_passed"
    assert session["explicit_abstention"] is True
    assert session["operator_review_required"] is True
    assert session["actual_tool_executed"] is False
    assert attestation["synthetic"] is True
    assert attestation["runtime_effect"] is False
    assert finding["actual_execution_verified"] is False
