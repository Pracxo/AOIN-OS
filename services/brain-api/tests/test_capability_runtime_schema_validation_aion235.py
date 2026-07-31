from __future__ import annotations

import pytest
from capability_runtime_test_support import load_runtime


def test_restricted_schema_subset_validates_documents() -> None:
    runtime = load_runtime()
    schema = {
        "type": "object",
        "properties": {
            "status": {"type": "string", "enum": ["ok"]},
            "count": {"type": "integer", "minimum": 1, "maximum": 2},
        },
        "required": ["status", "count"],
        "additionalProperties": False,
    }
    assert runtime.validate_json_against_schema({"status": "ok", "count": 1}, schema) == []
    assert runtime.validate_json_against_schema({"status": "bad", "count": 3}, schema)


def test_schema_rejects_external_refs_and_unknown_keywords() -> None:
    runtime = load_runtime()
    with pytest.raises(ValueError):
        runtime.CapabilityInputSchema.create(
            schema_id="bad-input",
            capability_id="capability.text.normalize",
            schema={"type": "object", "$ref": "https://example.invalid/schema"},
        )
    with pytest.raises(ValueError):
        runtime.CapabilityInputSchema.create(
            schema_id="bad-input-2",
            capability_id="capability.text.normalize",
            schema={"type": "string", "contentEncoding": "base64"},
        )


def test_runtime_rejects_oversized_depth_and_protected_material() -> None:
    runtime, service, session = __import__(
        "capability_runtime_test_support",
        fromlist=["new_service"],
    ).new_service()
    document = {}
    cursor = document
    for index in range(18):
        cursor["nested"] = {"level": index}
        cursor = cursor["nested"]
    with pytest.raises(runtime.CapabilityRuntimeRejected):
        service.execute(
            session_id=session.session_id,
            request_id="bad-depth",
            capability_id="capability.json.validate",
            input_payload={
                "document": document,
                "schema": {"type": "object", "additionalProperties": True},
            },
        )
    with pytest.raises(runtime.CapabilityRuntimeRejected):
        service.execute(
            session_id=session.session_id,
            request_id="bad-marker",
            capability_id="capability.text.normalize",
            input_payload={"text": "https://example.invalid"},
        )
