"""Threat model service tests."""

from __future__ import annotations

from tests.security_fakes import SCOPE, services


def test_threat_model_service_seeds_generic_defaults() -> None:
    _, _, threat_model, *_ = services()

    result = threat_model.seed_defaults(dry_run=True, owner_scope=SCOPE)

    assert result["threat_model_count"] >= 1


def test_threat_model_defaults_contain_no_domain_terms() -> None:
    _, _, threat_model, *_ = services()

    result = threat_model.seed_defaults(dry_run=True, owner_scope=SCOPE)
    joined = " ".join(result["threat_model_ids"]).lower()  # type: ignore[arg-type]

    for term in {"finance", "trading", "legal", "healthcare", "medical", "procurement"}:
        assert term not in joined
