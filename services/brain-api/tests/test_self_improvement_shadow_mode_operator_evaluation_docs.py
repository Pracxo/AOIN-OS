"""AION-179 shadow-mode operator evaluation documentation tests."""

from __future__ import annotations

import json
import os
import stat
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/lib"))

from self_improvement_governance import (  # noqa: E402
    AION179_REQUIRED_DOCS,
    AION179_REQUIRED_EXAMPLES,
    SHADOW_OPERATOR_EVALUATION_DECISION,
    SHADOW_OPERATOR_EVALUATION_ID,
    validate_shadow_operator_evaluation_report,
)


def test_shadow_operator_evaluation_artifacts_are_present() -> None:
    for relative in (*AION179_REQUIRED_DOCS, *AION179_REQUIRED_EXAMPLES):
        assert (ROOT / relative).is_file(), relative

    adr_index = (ROOT / "docs/adr/README.md").read_text()
    assert "0164-controlled-shadow-mode-operator-evaluation.md" in adr_index


def test_shadow_operator_evaluation_report_records_pass() -> None:
    payload = _json("examples/self-improvement/shadow-mode-operator-evaluation-report.json")
    validate_shadow_operator_evaluation_report(payload)

    assert payload["evaluation_id"] == SHADOW_OPERATOR_EVALUATION_ID
    assert payload["decision"] == SHADOW_OPERATOR_EVALUATION_DECISION
    assert payload["scenario_count"] == 14
    assert all(item["passed"] for item in payload["scenario_results"])
    assert payload["repository_digest_before"] == payload["repository_digest_after"]


def test_shadow_operator_evaluation_scripts_are_executable() -> None:
    for relative in (
        "scripts/lib/self_improvement_shadow_operator_evaluation.py",
        "scripts/self-improvement-shadow-mode-operator-evaluation-no-go-regression.sh",
        "scripts/self-improvement-shadow-mode-operator-evaluation-check.sh",
    ):
        mode = os.stat(ROOT / relative).st_mode
        assert mode & stat.S_IXUSR, relative


def _json(relative: str) -> dict[str, Any]:
    with (ROOT / relative).open() as handle:
        payload = json.load(handle)
    assert isinstance(payload, dict)
    return payload
