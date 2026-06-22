from __future__ import annotations

from tests.kernel_fakes import kernel_container


def test_kernel_diagnostics_include_outcome_checks() -> None:
    checks = kernel_container().diagnostics.run()
    names = {check.name for check in checks}

    assert "outcomes_enabled" in names
    assert "effect_verification_enabled" in names
    assert "outcome_services_present" in names
