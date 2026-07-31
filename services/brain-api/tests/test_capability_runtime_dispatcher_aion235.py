from __future__ import annotations

from capability_runtime_test_support import new_service


def test_static_dispatcher_executes_six_reference_capabilities_and_two_connector_ops() -> None:
    runtime, service, session = new_service()
    operations = [
        ("capability_runtime.health.read", {}),
        ("capability_runtime.observability.read", {}),
        ("capability_runtime.audit.read", {}),
        ("capability.text.normalize", {"text": "AION\r\nOS"}),
        ("capability.hash.sha256", {"text": "AION-235"}),
        (
            "capability.json.validate",
            {
                "document": {"status": "ok"},
                "schema": {
                    "type": "object",
                    "properties": {"status": {"type": "string", "const": "ok"}},
                    "required": ["status"],
                    "additionalProperties": False,
                },
            },
        ),
        (
            "connector.reference.read.simulate",
            {"fixture_id": "reference-fixture-AION-235", "record_key": "record-001"},
        ),
        (
            "connector.reference.write.preview",
            {
                "fixture_id": "reference-fixture-AION-235",
                "record_key": "record-001",
                "proposed_value": {"status": "previewed"},
            },
        ),
    ]
    results = [
        service.execute(
            session_id=session.session_id,
            request_id=f"dispatch-{index}",
            capability_id=capability_id,
            input_payload=payload,
        )
        for index, (capability_id, payload) in enumerate(operations, start=1)
    ]
    assert len(results) == 8
    assert all(item.output_validation.passed for item in results)
    assert results[3].output["normalized_text"] == "AION\nOS"
    assert results[4].output["sha256"] == (
        "0d162cdfbe8fd1e024840bc98874a94f9b5bb509f2ea21b638c956e61fb496a5"
    )
    assert results[6].status == runtime.CapabilityExecutionStatus.simulated
    assert results[7].status == runtime.CapabilityExecutionStatus.previewed
    assert results[7].output["mutation_applied"] is False
    service.close_session(session.session_id)
    assert service.session_repository.active_count() == 0


def test_dispatcher_exposes_static_mapping_only() -> None:
    runtime = __import__(
        "aion_brain.contracts.sandboxed_capability_runtime",
        fromlist=["DeterministicStaticCapabilityDispatcher"],
    )
    dispatcher = runtime.DeterministicStaticCapabilityDispatcher()
    assert dispatcher.allowed_capability_ids == set(runtime.CAPABILITY_MANIFEST_BY_ID)
