"""Deterministic Golden Path assertion engine."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.golden_path import GoldenPathAssertionResult
from aion_brain.golden_path.redaction import redact_golden_path_payload

_SECRET_KEY_PARTS = {
    "api_key",
    "apikey",
    "authorization",
    "bearer",
    "client_secret",
    "credential",
    "password",
    "private_key",
    "secret",
    "token",
}
_BANNED_DOMAIN_TERMS = {
    "finance",
    "trading",
    "legal",
    "healthcare",
    "medical",
    "payments",
    "payment",
    "procurement",
    "human_resources",
}


class AssertionEngine:
    """Evaluate assertion dictionaries without eval or dynamic code execution."""

    def evaluate_assertion(
        self,
        assertion: dict[str, Any],
        context: dict[str, Any],
    ) -> GoldenPathAssertionResult:
        """Evaluate one assertion and fail closed on unknown assertion types."""

        assertion_type = str(assertion.get("assertion_type", "generic"))
        assertion_key = str(assertion.get("assertion_key") or f"assertion-{uuid4().hex}")
        expected_value = assertion.get("expected")
        path = str(assertion.get("path", ""))
        actual_value = _lookup(context, path) if path else context
        passed = False
        message = "Assertion passed."

        if assertion_type == "status_equals":
            passed = actual_value == expected_value
            message = f"Expected status {expected_value}."
        elif assertion_type == "field_present":
            passed = actual_value is not None
            message = f"Expected field {path} to be present."
        elif assertion_type == "field_absent":
            passed = actual_value is None
            message = f"Expected field {path} to be absent."
        elif assertion_type == "count_at_least":
            passed = _count(actual_value) >= int(expected_value or 0)
            message = f"Expected count at least {expected_value}."
        elif assertion_type == "count_equals":
            passed = _count(actual_value) == int(expected_value or 0)
            message = f"Expected count equal to {expected_value}."
        elif assertion_type == "boolean_true":
            passed = actual_value is True
            message = f"Expected {path} to be true."
        elif assertion_type == "boolean_false":
            passed = actual_value is False
            message = f"Expected {path} to be false."
        elif assertion_type == "no_external_call":
            passed = not bool(context.get("external_calls"))
            message = "Expected no external calls."
        elif assertion_type == "no_execution":
            passed = not bool(context.get("executed")) and not bool(context.get("tool_execution"))
            message = "Expected no execution."
        elif assertion_type == "no_secret":
            passed = not _contains_secret(context)
            message = "Expected no sensitive payload markers."
        elif assertion_type == "no_hidden_reasoning":
            passed = not _contains_hidden_reasoning(context)
            message = "Expected no private trace markers."
        elif assertion_type == "no_domain_drift":
            passed = not _contains_domain_term(context)
            message = "Expected no domain-specific drift."
        elif assertion_type == "policy_allowed":
            passed = bool(actual_value)
            message = "Expected policy allow."
        elif assertion_type == "policy_denied":
            passed = actual_value is False
            message = "Expected policy deny."
        elif assertion_type == "generic":
            passed = True
            message = "Generic assertion recorded."
        else:
            passed = False
            message = f"Unknown assertion type denied: {assertion_type}."
            assertion_type = "generic"

        status = "passed" if passed else "failed"
        severity = str(assertion.get("severity", "medium"))
        if severity not in {"low", "medium", "high", "critical"}:
            severity = "medium"
        return GoldenPathAssertionResult(
            assertion_result_id=f"golden-assertion-{uuid4().hex}",
            golden_path_run_id=str(context.get("golden_path_run_id", "golden-path-run")),
            golden_path_scenario_id=str(
                context.get("golden_path_scenario_id", "golden-path-scenario")
            ),
            step_result_id=cast(str | None, context.get("step_result_id")),
            trace_id=cast(str | None, context.get("trace_id")),
            assertion_key=assertion_key,
            assertion_type=cast(Any, assertion_type),
            status=cast(Any, status),
            expected={"value": _safe_result_value(expected_value)},
            actual={"value": _safe_result_value(actual_value)},
            message=message,
            severity=cast(Any, severity),
            metadata={"path": path, "fail_closed": not passed},
            created_at=datetime.now(UTC),
        )

    def evaluate_many(
        self,
        assertions: list[dict[str, Any]],
        context: dict[str, Any],
    ) -> list[GoldenPathAssertionResult]:
        """Evaluate assertion dictionaries."""

        return [self.evaluate_assertion(assertion, context) for assertion in assertions]


def _lookup(context: dict[str, Any], path: str) -> object | None:
    if not path:
        return context
    current: object = context
    for part in path.split("."):
        if isinstance(current, dict):
            current = current.get(part)
        elif isinstance(current, list) and part.isdigit():
            index = int(part)
            current = current[index] if index < len(current) else None
        else:
            return None
        if current is None:
            return None
    return current


def _count(value: object) -> int:
    if isinstance(value, (list, tuple, set, dict, str)):
        return len(value)
    if value is None:
        return 0
    return 1


def _contains_secret(value: object) -> bool:
    if isinstance(value, dict):
        for key, nested in value.items():
            lowered = str(key).lower().replace("-", "_")
            if any(part in lowered for part in _SECRET_KEY_PARTS):
                return True
            if _contains_secret(nested):
                return True
    elif isinstance(value, list):
        return any(_contains_secret(item) for item in value)
    elif isinstance(value, str):
        lowered = value.lower()
        return any(marker in lowered for marker in ("sk-", "xoxb-", "ghp_"))
    return False


def _contains_hidden_reasoning(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_hidden_reasoning(key) or _contains_hidden_reasoning(item)
            for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_hidden_reasoning(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return "hidden_reasoning" in lowered or "chain_of_thought" in lowered
    return False


def _contains_domain_term(value: object) -> bool:
    if isinstance(value, dict):
        return any(
            _contains_domain_term(key) or _contains_domain_term(item) for key, item in value.items()
        )
    if isinstance(value, list):
        return any(_contains_domain_term(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower().replace("-", "_")
        return any(term in lowered for term in _BANNED_DOMAIN_TERMS)
    return False


def _safe_result_value(value: object) -> object:
    if _contains_secret(value) or _contains_hidden_reasoning(value):
        return {"redacted": True, "reason": "safety_marker_detected"}
    return redact_golden_path_payload(value)


__all__ = ["AssertionEngine"]
