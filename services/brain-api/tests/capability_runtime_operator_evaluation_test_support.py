from __future__ import annotations

import importlib.util
from functools import cache
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
PILOT_EVIDENCE_PATH = (
    "examples/secure-runtime-integration/"
    "capability-runtime-local-sandbox-pilot-evidence.json"
)


@cache
def evaluation_module():
    module_path = REPO_ROOT / "scripts/lib/capability_runtime_operator_evaluation.py"
    spec = importlib.util.spec_from_file_location(
        "capability_runtime_operator_evaluation", module_path
    )
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@cache
def evaluation_report():
    module = evaluation_module()
    committed_report = (
        REPO_ROOT
        / "examples/secure-runtime-integration/capability-runtime-operator-evaluation-report.json"
    )
    if committed_report.exists():
        import json

        report = json.loads(committed_report.read_text(encoding="utf-8"))
        module.validate_report(report)
        return report
    report = module.evaluate(
        repo_root=REPO_ROOT,
        evaluation_id=module.EVALUATION_ID,
        implementation_main_commit=module.IMPLEMENTATION_MERGE_COMMIT,
        evaluation_base_commit="unit-test-base",
        pilot_evidence_path=REPO_ROOT / PILOT_EVIDENCE_PATH,
        temporary_output_directory=Path("/tmp/aion-capability-runtime-evaluation-tests"),
    )
    module.validate_report(report)
    return report


def scenario(scenario_id: str):
    for item in evaluation_report()["scenarios"]:
        if item["scenario_id"] == scenario_id:
            return item
    raise AssertionError(f"missing scenario {scenario_id}")


def assert_scenario_passes(scenario_id: str):
    item = scenario(scenario_id)
    assert item["status"] == "pass"
    failed = [check["name"] for check in item["checks"] if not check["passed"]]
    assert failed == []
    return item
