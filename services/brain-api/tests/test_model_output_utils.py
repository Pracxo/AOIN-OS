"""Model output utility tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.model_outputs import ModelOutputRecord
from aion_brain.model_outputs.hash import hash_model_output
from aion_brain.model_outputs.parser import OutputParser
from aion_brain.model_outputs.redaction import redact_model_output, redact_output_payload
from aion_brain.model_outputs.unsafe_detector import UnsafeOutputDetector
from tests.model_outputs_fakes import repository


def test_hash_normalizes_line_endings() -> None:
    assert hash_model_output("hello\r\nworld  ") == hash_model_output("hello\nworld")


def test_redaction_removes_secret_values_and_hidden_markers() -> None:
    redacted, findings = redact_model_output("hidden reasoning: x\npassword: swordfish")

    assert "hidden reasoning" not in redacted.lower()
    assert "swordfish" not in redacted
    assert {finding["code"] for finding in findings} == {
        "protected_reasoning_removed",
        "secret_like_value_redacted",
    }


def test_payload_redaction_replaces_secret_keys() -> None:
    redacted, findings = redact_output_payload({"password": "secret", "safe": "ok"})

    assert "password" not in redacted
    assert redacted["safe"] == "ok"
    assert findings


def test_unsafe_detector_flags_tool_execution_instruction() -> None:
    findings = UnsafeOutputDetector().detect("execute the tool now")

    assert any(finding["code"] == "tool_execution_instruction" for finding in findings)


def test_output_parser_extracts_json_and_tool_segments() -> None:
    output = ModelOutputRecord(
        model_output_id="output-1",
        trace_id="trace-1",
        status="received",
        output_type="mixed",
        raw_output_hash="hash",
        redacted_output='```json\n{"content":"ok"}\n```\ntool: echo {"value":"ok"}',
        output_redacted=False,
        token_estimate=10,
        char_count=50,
        created_at=datetime.now(UTC),
    )

    segments = OutputParser().parse(output)

    assert {segment.segment_type for segment in segments} >= {"json_block", "tool_intent"}


def test_structured_validation_rejects_missing_json() -> None:
    from aion_brain.model_outputs.structured_validator import StructuredOutputValidator

    repo = repository()
    repo.save_output(
        ModelOutputRecord(
            model_output_id="output-1",
            status="received",
            output_type="text",
            raw_output_hash="hash",
            redacted_output="plain text",
            output_redacted=False,
            token_estimate=2,
            char_count=10,
        )
    )

    validation = StructuredOutputValidator(repo).validate("output-1", "generic_json")

    assert validation.valid is False
    assert validation.schema_errors[0]["code"] == "json_parse_failed"
