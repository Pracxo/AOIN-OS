from secure_runtime_aion232_test_helpers import report


def test_pilot_evidence_schema_fingerprint_and_counts_are_reconciled() -> None:
    pilot = report()["pilot_validation"]
    assert pilot["passed"] is True
    assert pilot["pilot_id"] == "AION-231-controlled-local-operator-runtime-pilot"
    assert (
        pilot["report_fingerprint"]
        == "05b78f220cc0d4870097a2426c47e1cf98b09a17a55e01625a9adea288297a6b"
    )
    checks = pilot["checks"]
    for key in (
        "identity_assertions_verified_exact",
        "exact_replays_rejected_exact",
        "request_identity_bindings_exact",
        "actor_context_bindings_exact",
        "sessions_started_exact",
        "sessions_closed_exact",
        "active_sessions_after_close_exact",
        "active_requests_after_close_exact",
        "simulated_dispatches_exact",
        "protected_material_absent",
    ):
        assert checks[key] is True
