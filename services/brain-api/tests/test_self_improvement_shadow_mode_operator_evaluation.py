"""AION-179 shadow-mode operator evaluation harness tests."""

from __future__ import annotations

from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
HARNESS_DIR = ROOT / "scripts" / "lib"

import sys

if str(HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(HARNESS_DIR))

from self_improvement_shadow_operator_evaluation import (  # noqa: E402
    EXPECTED_BASE_COMMIT,
    PASS_DECISION,
    SCENARIO_IDS,
    build_report,
)


def test_shadow_operator_evaluation_harness_records_pass(tmp_path: Path) -> None:
    report = build_report(
        repo_root=ROOT,
        evaluation_id="AION-SOE-001",
        evaluation_base_commit=EXPECTED_BASE_COMMIT,
        temporary_output_directory=tmp_path,
    )

    assert report["decision"] == PASS_DECISION
    assert report["scenario_count"] == len(SCENARIO_IDS)
    assert tuple(item["scenario_id"] for item in report["scenario_results"]) == SCENARIO_IDS
    assert all(item["passed"] for item in report["scenario_results"])
    assert all(report["hard_gates"].values())
    assert report["repository_digest_before"] == report["repository_digest_after"]


def test_shadow_operator_evaluation_harness_fails_closed_for_wrong_base(
    tmp_path: Path,
) -> None:
    with pytest.raises(ValueError, match="evaluation base commit"):
        build_report(
            repo_root=ROOT,
            evaluation_id="AION-SOE-001",
            evaluation_base_commit="0" * 40,
            temporary_output_directory=tmp_path,
        )


def test_shadow_operator_evaluation_harness_import_boundary() -> None:
    text = (HARNESS_DIR / "self_improvement_shadow_operator_evaluation.py").read_text()
    forbidden = (
        "import subprocess",
        "import socket",
        "import requests",
        "import httpx",
        "import aiohttp",
        "import git",
        "import github",
    )

    for marker in forbidden:
        assert marker not in text
    assert "ControlledShadowModeRunner" in text
    assert "replay_shadow_run" in text
