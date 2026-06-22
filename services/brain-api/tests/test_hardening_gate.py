"""Hardening gate tests."""

from __future__ import annotations

from aion_brain.contracts.security_baseline import HardeningGateRequest, SecurityScanRequest
from tests.security_fakes import SCOPE, services, settings


def test_hardening_gate_service_passes_with_fake_clean_checks(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / ".env.example").write_text("AION_ENV=development\n", encoding="utf-8")
    _, _, threat_model, controls, hardening, _ = services(root_dir=tmp_path)
    threat_model.seed_defaults(dry_run=False, owner_scope=SCOPE)
    controls.seed_defaults(dry_run=False)

    run = hardening.run(
        HardeningGateRequest(
            owner_scope=SCOPE,
            include_secret_scan=False,
            include_api_exposure_check=False,
            include_policy_coverage_check=False,
        )
    )

    assert run.status == "passed"


def test_hardening_gate_service_fails_with_high_secret_finding(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / ".env.example").write_text("AION_ENV=development\n", encoding="utf-8")
    source_dir = tmp_path / "services" / "brain-api" / "src"
    source_dir.mkdir(parents=True)
    (source_dir / "app.py").write_text('API_KEY = "sk-failsecret1234567890"\n', encoding="utf-8")
    _, _, threat_model, controls, hardening, _ = services(root_dir=tmp_path)
    threat_model.seed_defaults(dry_run=False, owner_scope=SCOPE)
    controls.seed_defaults(dry_run=False)

    run = hardening.run(
        HardeningGateRequest(
            owner_scope=SCOPE,
            include_api_exposure_check=False,
            include_policy_coverage_check=False,
        )
    )

    assert run.status == "failed"


def test_hardening_gate_service_fails_with_full_autonomy_default(tmp_path) -> None:  # type: ignore[no-untyped-def]
    (tmp_path / ".env.example").write_text("AION_ENV=development\n", encoding="utf-8")
    configured = settings(AION_AUTONOMY_DEFAULT_MAX_MODE="full")
    _, _, threat_model, controls, hardening, _ = services(
        root_dir=tmp_path,
        configured_settings=configured,
    )
    threat_model.seed_defaults(dry_run=False, owner_scope=SCOPE)
    controls.seed_defaults(dry_run=False)

    run = hardening.run(
        HardeningGateRequest(
            owner_scope=SCOPE,
            include_secret_scan=False,
            include_api_exposure_check=False,
            include_policy_coverage_check=False,
        )
    )

    assert run.status == "failed"


def test_visual_telemetry_emits_security_events(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "app.py"
    target.write_text('API_KEY = "sk-telemetry1234567890"\n', encoding="utf-8")
    _, scanner, *_rest, telemetry = services(root_dir=tmp_path)

    scanner.scan(SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=[str(target)]))

    event_types = {getattr(event, "event_type", "") for event in telemetry.events}
    assert "security_scan_started" in event_types
    assert "security_finding_detected" in event_types
