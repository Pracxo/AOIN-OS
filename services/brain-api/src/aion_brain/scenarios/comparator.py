"""Deterministic scenario output comparison."""

from typing import Any

from aion_brain.contracts.scenarios import ScenarioRun

DYNAMIC_KEYS = {
    "created_at",
    "updated_at",
    "completed_at",
    "trace_id",
    "request_id",
    "correlation_id",
    "decision_id",
    "scenario_run_id",
    "scenario_step_run_id",
}


class ScenarioComparator:
    """Compare scenario results without fuzzy or model-assisted semantics."""

    def compare_step_output(
        self,
        output: dict[str, Any],
        expected: dict[str, Any],
    ) -> dict[str, Any]:
        """Compare one step output with deterministic expectation rules."""
        normalized = _strip_dynamic(output)
        failures: list[str] = []

        status = expected.get("status")
        if isinstance(status, str) and output.get("status") != status:
            failures.append(f"status:{status}")

        for key in _string_list(expected.get("required_keys")):
            if key not in normalized and key not in output:
                failures.append(f"missing_required_key:{key}")

        for key in _string_list(expected.get("forbidden_keys")):
            if key in normalized or key in output:
                failures.append(f"forbidden_key_present:{key}")

        equals = expected.get("equals")
        if isinstance(equals, dict):
            for key, value in equals.items():
                if _get_path(normalized, str(key)) != value:
                    failures.append(f"equals_mismatch:{key}")

        contains = expected.get("contains")
        if isinstance(contains, dict):
            for key, value in contains.items():
                actual = _get_path(normalized, str(key))
                if isinstance(actual, str):
                    if str(value) not in actual:
                        failures.append(f"contains_mismatch:{key}")
                elif isinstance(actual, list):
                    if value not in actual:
                        failures.append(f"contains_mismatch:{key}")
                else:
                    failures.append(f"contains_mismatch:{key}")

        min_count = expected.get("min_count")
        if isinstance(min_count, int) and _countable_size(output) < min_count:
            failures.append("min_count_not_met")

        max_count = expected.get("max_count")
        if isinstance(max_count, int) and _countable_size(output) > max_count:
            failures.append("max_count_exceeded")

        return {
            "passed": not failures,
            "failures": failures,
            "ignored_dynamic_fields": sorted(DYNAMIC_KEYS),
        }

    def compare_run(self, run: ScenarioRun, expected: dict[str, Any]) -> dict[str, Any]:
        """Compare an entire run against deterministic expectations."""
        failures: list[str] = []
        status = expected.get("status")
        if isinstance(status, str) and run.status != status:
            failures.append(f"status:{status}")
        min_count = expected.get("min_count")
        if isinstance(min_count, int) and run.passed_steps < min_count:
            failures.append("min_count_not_met")
        max_count = expected.get("max_count")
        if isinstance(max_count, int) and run.failed_steps > max_count:
            failures.append("max_count_exceeded")
        required_keys = _string_list(expected.get("required_keys"))
        for key in required_keys:
            if key not in run.result:
                failures.append(f"missing_required_key:{key}")
        return {
            "passed": not failures,
            "failures": failures,
            "status": run.status,
            "step_count": run.step_count,
            "passed_steps": run.passed_steps,
            "failed_steps": run.failed_steps,
            "skipped_steps": run.skipped_steps,
        }


def _strip_dynamic(value: Any) -> Any:
    if isinstance(value, dict):
        return {
            key: _strip_dynamic(item)
            for key, item in value.items()
            if key not in DYNAMIC_KEYS and not _is_implicit_id_key(key)
        }
    if isinstance(value, list):
        return [_strip_dynamic(item) for item in value]
    return value


def _is_implicit_id_key(key: str) -> bool:
    return key.endswith("_id") and key not in {"node_id", "edge_id", "step_id"}


def _get_path(value: dict[str, Any], path: str) -> Any:
    current: Any = value
    for part in path.split("."):
        if not isinstance(current, dict) or part not in current:
            return None
        current = current[part]
    return current


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item) for item in value]


def _countable_size(value: object) -> int:
    if isinstance(value, dict):
        for key in ("items", "records", "results", "steps"):
            item = value.get(key)
            if isinstance(item, list):
                return len(item)
        return len(value)
    if isinstance(value, list):
        return len(value)
    return 1 if value is not None else 0
