from secure_runtime_aion232_test_helpers import scenario


def test_audit_observability_health_and_checkpoint_integrity() -> None:
    audit = scenario("audit_chain_integrity")["requirements"]
    assert audit["append_only_in_memory_audit"] is True
    assert audit["missing_record_detected"] is True
    assert audit["reordered_record_detected"] is True
    assert audit["changed_record_detected"] is True
    assert audit["protected_material_absent"] is True
    obs = scenario("observability_health_and_checkpoint_integrity")["requirements"]
    assert obs["observability_contains_safe_counts_only"] is True
    assert obs["health_readiness_requires_exact_authorization_and_clear_kill_switch"] is True
    assert obs["no_checkpoint_file_retained"] is True
    assert obs["no_external_telemetry_exporter"] is True
