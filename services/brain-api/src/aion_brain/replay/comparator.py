"""Deterministic semantic comparison for Brain snapshots."""

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.replay import BrainSnapshot, TraceComparison

DEFAULT_IGNORED_FIELDS = [
    "created_at",
    "updated_at",
    "timestamp",
    "trace_id",
    "replay_trace_id",
    "snapshot_id",
    "content_hash",
    "telemetry_id",
    "observability_event_id",
    "model_call_id",
    "reasoning_id",
    "evaluation_id",
    "learning_id",
    "correlation_id",
]


class TraceComparator:
    """Compare normalized AION snapshot semantics without model calls."""

    def compare(
        self,
        source: BrainSnapshot,
        replay: BrainSnapshot,
        ignored_fields: list[str] | None = None,
    ) -> TraceComparison:
        """Return a stable semantic diff and drift score."""
        ignored = ignored_fields if ignored_fields is not None else DEFAULT_IGNORED_FIELDS
        source_state = _normalize(source.state, set(ignored), "")
        replay_state = _normalize(replay.state, set(ignored), "")
        differences: list[dict[str, Any]] = []
        _compare_values(source_state, replay_state, "state", differences)
        drift_detected = any(item["severity"] == "high" for item in differences)
        penalty = sum(_penalty(str(item["severity"])) for item in differences)
        score = max(0.0, min(1.0, 1.0 - penalty))
        return TraceComparison(
            comparison_id=f"comparison-{uuid4().hex}",
            source_trace_id=source.trace_id or "",
            replay_trace_id=replay.trace_id,
            source_snapshot_id=source.snapshot_id,
            replay_snapshot_id=replay.snapshot_id,
            matched=not differences,
            drift_detected=drift_detected,
            score=score,
            differences=differences,
            ignored_fields=list(ignored),
            created_at=datetime.now(UTC),
        )


def _normalize(value: Any, ignored: set[str], path: str) -> Any:
    if isinstance(value, dict):
        return {
            str(key): _normalize(item, ignored, f"{path}.{key}")
            for key, item in sorted(value.items())
            if str(key) not in ignored
        }
    if isinstance(value, list):
        normalized = [_normalize(item, ignored, f"{path}[]") for item in value]
        if _unordered_id_list(value, path):
            return sorted(normalized, key=str)
        return normalized
    return value


def _unordered_id_list(value: list[Any], path: str) -> bool:
    if "steps" in path or "timeline" in path or "events" in path:
        return False
    return all(isinstance(item, str) for item in value) and (
        path.endswith("_refs") or path.endswith("_ids")
    )


def _compare_values(
    source: Any,
    replay: Any,
    path: str,
    differences: list[dict[str, Any]],
) -> None:
    if isinstance(source, dict) and isinstance(replay, dict):
        for key in sorted(set(source) | set(replay)):
            child_path = f"{path}.{key}"
            if key not in source:
                _difference(child_path, None, replay[key], differences, "section_added")
            elif key not in replay:
                _difference(child_path, source[key], None, differences, "required_section_missing")
            else:
                _compare_values(source[key], replay[key], child_path, differences)
        return
    if isinstance(source, list) and isinstance(replay, list):
        for index in range(max(len(source), len(replay))):
            child_path = f"{path}[{index}]"
            if index >= len(source):
                _difference(child_path, None, replay[index], differences, "item_added")
            elif index >= len(replay):
                _difference(child_path, source[index], None, differences, "required_item_missing")
            else:
                _compare_values(source[index], replay[index], child_path, differences)
        return
    if source != replay:
        reason = _reason(path, source, replay)
        _difference(path, source, replay, differences, reason)


def _difference(
    path: str,
    source: Any,
    replay: Any,
    differences: list[dict[str, Any]],
    reason: str,
) -> None:
    differences.append(
        {
            "path": path,
            "source": source,
            "replay": replay,
            "severity": _severity(path, source, replay, reason),
            "reason": reason,
        }
    )


def _reason(path: str, source: Any, replay: Any) -> str:
    if path.endswith("outcome.status"):
        return "outcome_status_changed"
    if "plan" in path and path.endswith("action_type"):
        return "plan_action_changed"
    if "policy" in path and path.endswith("allow"):
        return "policy_outcome_changed"
    if "evaluation" in path and isinstance(source, int | float) and isinstance(
        replay, int | float
    ):
        return "evaluation_score_changed"
    return "semantic_value_changed"


def _severity(path: str, source: Any, replay: Any, reason: str) -> str:
    if reason in {
        "outcome_status_changed",
        "plan_action_changed",
        "policy_outcome_changed",
    }:
        return "high"
    if reason == "required_section_missing" and path.count(".") <= 2:
        return "high"
    if reason == "required_item_missing" and (
        "plan.steps" in path or "policy" in path
    ):
        return "high"
    if (
        "evaluation" in path
        and isinstance(source, int | float)
        and isinstance(replay, int | float)
        and abs(float(source) - float(replay)) > 0.2
    ):
        return "high"
    if "risk_level" in path or "constraints" in path:
        return "medium"
    return "low"


def _penalty(severity: str) -> float:
    return {"high": 0.25, "medium": 0.1, "low": 0.02}.get(severity, 0.02)
