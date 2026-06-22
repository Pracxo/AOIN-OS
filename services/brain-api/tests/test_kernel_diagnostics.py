"""Kernel diagnostic tests."""

from tests.kernel_fakes import kernel_container


def test_diagnostics_are_deterministic_and_secret_free() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}
    assert checks
    assert all(check.status == "passed" for check in checks)
    assert "graphiti_enabled" in names
    assert "graphiti_package_available" in names
    assert "graphiti_selected" in names
    assert "graphiti_fallback_active" in names
    assert "graphiti_backend_type" in names
    assert "graphiti_llm_disabled" in names
    assert "policy_catalog_enabled" in names
    assert "policy_test_harness_enabled" in names
    assert "policy_bundle_export_enabled" in names
    assert "opa_status_check_enabled" in names
    assert "policy_catalog_service_present" in names
    assert "permission_matrix_service_present" in names
    assert "ci_quality_scripts_present" in names
    assert "release_check_script_present" in names
    assert "repo_health_script_present" in names
    assert "no_domain_drift_script_present" in names
    assert "operations_docs_present" in names
    assert "password" not in str([check.details for check in checks]).lower()
