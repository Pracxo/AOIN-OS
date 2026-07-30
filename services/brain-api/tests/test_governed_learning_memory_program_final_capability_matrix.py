from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_capability_matrix", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_capability_matrix_separates_implemented_disabled_and_future_charter() -> None:
    harness = _load_harness()
    matrix = harness.CAPABILITY_MATRIX
    assert "governed promotion planning" in matrix["implemented_and_evaluated"]
    assert "local append-only persistence" in matrix["implemented_and_evaluated"]
    assert "in-memory shadow overlays" in matrix["implemented_and_evaluated"]
    assert "public-network research execution" in matrix[
        "implemented_but_currently_unauthorized_for_new_live_execution"
    ]
    assert "production-memory writes" in matrix["disabled"]
    assert "model-weight training" in matrix["disabled"]
    assert "production runtime integration" in matrix[
        "requires_separate_future_program_charter"
    ]
