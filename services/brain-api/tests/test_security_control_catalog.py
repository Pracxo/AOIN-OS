"""Security control catalog tests."""

from __future__ import annotations

from tests.security_fakes import services


def test_security_control_catalog_seeds_defaults() -> None:
    _, _, _, controls, *_ = services()

    result = controls.seed_defaults(dry_run=True)

    assert result["control_count"] >= 1
    assert "policy.fail_closed" in result["control_keys"]
