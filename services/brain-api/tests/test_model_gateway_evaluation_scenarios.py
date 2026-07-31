from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
HARNESS = REPO_ROOT / "scripts/lib/model_gateway_operator_evaluation.py"
SAVED_REPORT = (
    REPO_ROOT / "examples/secure-runtime-integration/model-gateway-operator-evaluation-report.json"
)


def _load_harness():
    spec = importlib.util.spec_from_file_location("aion234_scenarios", HARNESS)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def test_evaluation_report_records_exact_pass_and_scenario_set(tmp_path: Path) -> None:
    harness = _load_harness()
    if SAVED_REPORT.exists():
        payload = json.loads(SAVED_REPORT.read_text(encoding="utf-8"))
    else:
        pilot_evidence = (
            REPO_ROOT
            / "examples/secure-runtime-integration/"
            "model-gateway-local-simulation-pilot-evidence.json"
        )
        payload = harness.evaluate_model_gateway_operator(
            repo_root=REPO_ROOT,
            evaluation_id="AION-SRIPE-002",
            evaluation_base_commit="48e9daebcac77aa48aa2336323c40eae948f3ac2",
            pilot_evidence=pilot_evidence,
            temporary_output_directory=tmp_path,
        )
    harness.validate_evaluation_report(payload)
    assert payload["decision"] == harness.DECISION_PASS
    assert payload["evaluation_passed"] is True
    assert payload["scenario_count"] == 28
    assert payload["scenario_ids"] == [item["scenario_id"] for item in payload["scenario_results"]]
    assert all(item["passed"] is True for item in payload["scenario_results"])
    assert all(item["passed"] is True for item in payload["hard_gate_results"])
    assert payload["next_architecture_decision"] == (
        "sandboxed_capability_runtime_implementation_authorized"
    )
