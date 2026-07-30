from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/governed_learning_memory_program_final_evaluation.py"


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion229_runtime_boundary", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_final_runtime_boundary_keeps_every_live_execution_authorization_disabled() -> None:
    harness = _load_harness()
    state = harness.runtime_authorization_state()
    assert state["production_runtime_authorized"] is False
    assert state["repeat_live_pilot_authorized"] is False
    assert state["active_continual_learning_execution_authorization"] is False
    assert state["operator_invoked_continual_learning_pilot_available"] is False
    assert all(value is False for value in state.values())
