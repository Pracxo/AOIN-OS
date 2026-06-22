"""Deterministic structured model output validation."""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.model_outputs import StructuredOutputValidation
from aion_brain.dialogue._shared import emit_telemetry
from aion_brain.model_outputs.redaction import redact_output_payload
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector

_JSON_BLOCK = re.compile(r"```json\n(?P<body>.*?)```", re.S | re.I)
_SCHEMA_KEYS: dict[str, set[str]] = {
    "response_candidate": {"content"},
    "explanation": {"summary"},
    "decision_recommendation": {"recommendation"},
    "tool_intent": {"intent_type"},
    "generic_json": set(),
}


class StructuredOutputValidator:
    """Validate JSON blocks against generic local schemas."""

    def __init__(
        self,
        repository: object,
        detector: UnsafeOutputDetector | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._detector = detector or UnsafeOutputDetector()
        self._telemetry_service = telemetry_service

    def validate(
        self,
        model_output_id: str,
        schema_name: str | None = None,
    ) -> StructuredOutputValidation:
        """Validate one model output's first JSON payload."""

        get_output = getattr(self._repository, "get_output", None)
        output = get_output(model_output_id) if callable(get_output) else None
        if output is None:
            raise ValueError("model_output_not_found")
        selected_schema = schema_name or "generic_json"
        errors: list[dict[str, Any]] = []
        warnings: list[dict[str, Any]] = []
        safety_errors: list[dict[str, Any]] = []
        parsed: dict[str, Any] = {}
        try:
            parsed = _extract_json_payload(output.redacted_output)
        except ValueError as exc:
            errors.append({"code": "json_parse_failed", "message": str(exc)})
        if selected_schema not in _SCHEMA_KEYS:
            errors.append({"code": "unsupported_schema", "schema_name": selected_schema})
        required = _SCHEMA_KEYS.get(selected_schema, set())
        missing = [key for key in required if key not in parsed]
        for key in missing:
            errors.append({"code": "missing_required_key", "key": key})
        clean_payload, redaction_findings = redact_output_payload(parsed)
        if redaction_findings:
            safety_errors.extend(redaction_findings)
            parsed = {}
        else:
            parsed = clean_payload
        for finding in self._detector.detect(json.dumps(parsed, sort_keys=True)):
            if finding["severity"] in {"high", "critical"}:
                safety_errors.append(finding)
            else:
                warnings.append(finding)
        valid = not errors and not safety_errors
        validation = StructuredOutputValidation(
            structured_validation_id=f"structured-validation-{uuid4().hex}",
            model_output_id=model_output_id,
            trace_id=output.trace_id,
            schema_name=selected_schema,
            status="passed" if valid else "failed",
            valid=valid,
            parsed_payload=parsed,
            schema_errors=errors,
            safety_errors=safety_errors,
            warnings=warnings,
            metadata={"deterministic_validator": True},
            created_at=datetime.now(UTC),
        )
        save = getattr(self._repository, "save_validation", None)
        result = save(validation) if callable(save) else validation
        stored = result if isinstance(result, StructuredOutputValidation) else validation
        emit_telemetry(
            self._telemetry_service,
            event_type="structured_output_validated",
            node_type="structured_validation",
            node_id=stored.structured_validation_id,
            intensity=0.6 if stored.valid else 0.9,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "schema_name": stored.schema_name},
        )
        return stored


def _extract_json_payload(text: str) -> dict[str, Any]:
    match = _JSON_BLOCK.search(text)
    candidate = match.group("body").strip() if match else text.strip()
    start = candidate.find("{")
    end = candidate.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise ValueError("no JSON object found")
    loaded = json.loads(candidate[start : end + 1])
    if not isinstance(loaded, dict):
        raise ValueError("JSON payload must be an object")
    return loaded


__all__ = ["StructuredOutputValidator"]
