"""Release handoff tests."""

from __future__ import annotations

from datetime import UTC, datetime

from aion_brain.contracts.release_package import ReleasePackageValidation
from aion_brain.release_package.handoff import ReleaseHandoffService


def test_release_handoff_report_lists_local_verification_commands() -> None:
    validation = ReleasePackageValidation(
        status="passed",
        checks=[],
        failures=[],
        warnings=[],
        generated_at=datetime.now(UTC),
    )

    report = ReleaseHandoffService().build("0.1.0", validation, {"release_baseline": {}})

    assert report.status == "ready"
    assert "scripts/check.sh" in report.local_verification_commands
    assert "local-first only" in report.known_limits
    assert report.included_reports["release_baseline"]["present"] is True
