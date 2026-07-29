from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from aion_brain.contracts.governed_engagement_learning import load_fixture_envelope

REPO_ROOT = Path(__file__).resolve().parents[3]
RUNNER = REPO_ROOT / "scripts/governed-learning-memory-engagement-shadow-run.py"


def test_fixture_loader_rejects_repository_paths():
    with pytest.raises(ValueError, match="outside repository"):
        load_fixture_envelope(
            REPO_ROOT
            / "examples/governed-learning-memory/engagement-application-result.json"
        )


def test_uninstalled_runner_writes_redacted_zero_effect_summary(tmp_path: Path):
    plan_path = tmp_path / "plan.json"
    fixture_path = tmp_path / "fixture.json"
    output_path = tmp_path / "shadow-summary.json"
    plan_path.write_text(
        json.dumps({"plan_id": "synthetic-shadow-plan", "records": []}) + "\n",
        encoding="utf-8",
    )
    fixture_path.write_text(
        json.dumps({"fixture_id": "synthetic-shadow-fixture", "records": []}) + "\n",
        encoding="utf-8",
    )

    completed = subprocess.run(
        [
            sys.executable,
            str(RUNNER),
            "--authorization",
            "AION-225-GLM-0003",
            "--plan",
            str(plan_path),
            "--fixture",
            str(fixture_path),
            "--output",
            str(output_path),
            "--confirm",
            "APPLY_ENGAGEMENT_SHADOW_OVERLAY",
            "--mode",
            "deterministic-simulation",
        ],
        cwd=REPO_ROOT,
        check=True,
        capture_output=True,
        text=True,
    )

    report = json.loads(output_path.read_text(encoding="utf-8"))
    assert "AION-226 engagement shadow summary" in completed.stdout
    assert report["authorization_id"] == "AION-225-GLM-0003"
    assert report["mode"] == "deterministic_simulation"
    assert report["redacted"] is True
    assert report["operator_invoked"] is True
    assert report["overlay_in_memory_only"] is True
    assert report["active_overlay_records_after_close"] == 0
    assert report["persistent_overlay_writes"] == 0
    assert report["aion_224_store_writes"] == 0
    assert report["production_policy_mutations"] == 0
    assert report["network_calls"] == 0
    assert report["runtime_effect"] is False
