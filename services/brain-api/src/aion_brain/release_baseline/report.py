"""Release baseline report helpers."""

from typing import Any

from aion_brain.contracts.scenarios import ScenarioRun

RECOMMENDATIONS = {
    "failed_scenarios": "review_failed_scenario_steps",
    "policy_coverage": "review_policy_coverage",
    "openapi_hygiene": "review_openapi_hygiene",
    "boundary_check": "review_boundary_violations",
    "kernel_self_test": "review_kernel_self_test",
    "contract_export": "export_contracts_before_release",
}


def build_release_report(
    scenario_runs: list[ScenarioRun],
    quality_gate_results: dict[str, Any],
) -> dict[str, Any]:
    """Build a deterministic release readiness summary."""
    failed_scenarios = [run.scenario_id for run in scenario_runs if run.status == "failed"]
    failed_steps = [
        {"scenario_run_id": run.scenario_run_id, "step_id": step.step_id}
        for run in scenario_runs
        for step in run.steps
        if step.status == "failed"
    ]
    gate_failures = [
        name
        for name, result in quality_gate_results.items()
        if isinstance(result, dict) and result.get("status") == "failed"
    ]
    recommendations = []
    if failed_scenarios:
        recommendations.append(RECOMMENDATIONS["failed_scenarios"])
    for name in gate_failures:
        if name in RECOMMENDATIONS:
            recommendations.append(RECOMMENDATIONS[name])
    if not recommendations:
        recommendations.append(RECOMMENDATIONS["contract_export"])
    passed = sum(run.status == "passed" for run in scenario_runs)
    total = len(scenario_runs)
    return {
        "scenario_count": total,
        "scenario_pass_rate": 1.0 if total == 0 else passed / total,
        "failed_scenarios": [item for item in failed_scenarios if item is not None],
        "failed_steps": failed_steps,
        "quality_gate_failures": gate_failures,
        "release_ready": not failed_scenarios and not gate_failures,
        "recommendations": recommendations,
    }
