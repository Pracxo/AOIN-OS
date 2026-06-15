"""Secret scanner tests."""

from __future__ import annotations

from aion_brain.contracts.security_baseline import SecurityScanRequest
from tests.security_fakes import SCOPE, services


def test_secret_scanner_detects_api_key_like_in_temp_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "app.py"
    target.write_text('API_KEY = "sk-testsecret1234567890"\n', encoding="utf-8")
    _, scanner, *_ = services(root_dir=tmp_path)

    run = scanner.scan(
        SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=[str(target)])
    )

    assert run.findings
    assert run.findings[0].finding_type == "api_key_like"


def test_secret_scanner_redacts_match(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "app.py"
    raw = "sk-redactiontarget1234567890"
    target.write_text(f'API_KEY = "{raw}"\n', encoding="utf-8")
    _, scanner, *_ = services(root_dir=tmp_path)

    run = scanner.scan(
        SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=[str(target)])
    )

    assert raw not in run.findings[0].redacted_match
    assert "***" in run.findings[0].redacted_match


def test_secret_scanner_respects_ignore_comment(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / "app.py"
    target.write_text(
        'API_KEY = "sk-ignoresecret1234567890"  # AION_SECRET_SCAN_IGNORE\n',
        encoding="utf-8",
    )
    _, scanner, *_ = services(root_dir=tmp_path)

    run = scanner.scan(
        SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=[str(target)])
    )

    assert run.findings == []


def test_secret_scanner_flags_env_file(tmp_path) -> None:  # type: ignore[no-untyped-def]
    target = tmp_path / ".env"
    target.write_text("AION_ENV=development\n", encoding="utf-8")
    _, scanner, *_ = services(root_dir=tmp_path)

    run = scanner.scan(
        SecurityScanRequest(scan_type="secrets", owner_scope=SCOPE, paths=[str(target)])
    )

    assert any(finding.finding_type == "env_file" for finding in run.findings)
