"""Generic deterministic regression report builder."""

from collections import Counter
from typing import Any

from aion_brain.contracts.regression import RegressionRunResult


class RegressionReportBuilder:
    """Summarize local regression results without domain-specific guidance."""

    def build(self, results: list[RegressionRunResult]) -> dict[str, Any]:
        """Return stable counts, common paths, and generic recommendations."""
        passed = sum(result.status == "passed" for result in results)
        failed = len(results) - passed
        drift = sum(result.drift_detected for result in results)
        paths = Counter(
            str(difference.get("path"))
            for result in results
            for difference in result.comparison.differences
        )
        worst_results = sorted(
            results,
            key=lambda result: (
                result.comparison.score,
                -len(result.comparison.differences),
            ),
        )[:5]
        worst = [
            {
                "case_id": result.case_id,
                "score": result.comparison.score,
                "difference_count": len(result.comparison.differences),
            }
            for result in worst_results
        ]
        return {
            "total_cases": len(results),
            "passed": passed,
            "failed": failed,
            "drift_detected": drift,
            "pass_rate": passed / len(results) if results else 0.0,
            "worst_cases": worst,
            "common_difference_paths": [
                {"path": path, "count": count} for path, count in paths.most_common(10)
            ],
            "recommendations": _recommendations(paths),
        }


def _recommendations(paths: Counter[str]) -> list[str]:
    recommendations: list[str] = []
    joined = " ".join(paths)
    if "policy" in joined:
        recommendations.append("review_policy_changes")
    if "plan" in joined:
        recommendations.append("review_planner_changes")
    if "context" in joined or "memory" in joined or "retrieval" in joined:
        recommendations.append("review_context_retrieval_changes")
    if "reasoning" in joined:
        recommendations.append("review_reasoning_changes")
    if paths:
        recommendations.append("update_expected_snapshot_if_change_is_intentional")
    return recommendations
