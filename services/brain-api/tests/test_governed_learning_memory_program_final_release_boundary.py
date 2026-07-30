from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"
LIVE_EVIDENCE = (
    REPO_ROOT
    / (
        "examples/governed-learning-memory/"
        "controlled-local-continual-learning-live-pilot-evidence.json"
    )
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_release_boundary", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_release_boundary_preserves_node24_and_v02_disabled(tmp_path: Path) -> None:
    harness = _load_harness()
    node24 = harness.validate_node24_baseline(REPO_ROOT)
    payload = harness.evaluate_program(
        repo_root=REPO_ROOT,
        evaluation_id="AION-GLMPE-004",
        evaluation_base_commit="0fc95c345c1f8daada58a5b45e6f3b1fdd33d9e0",
        live_evidence_path=LIVE_EVIDENCE,
        temporary_output_directory=tmp_path,
    )
    assert node24["supported_action_reference_count"] == 12
    assert payload["release_integrity"]["v02_release_ready"] is False
    assert payload["release_integrity"]["v02_tag_created"] is False
    assert payload["release_integrity"]["v02_release_created"] is False
