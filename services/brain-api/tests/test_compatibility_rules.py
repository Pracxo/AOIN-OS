"""Compatibility rule service tests."""

from __future__ import annotations

from aion_brain.contract_registry.rules import CompatibilityRuleService
from tests.contract_registry_helpers import SCOPE, AllowPolicy, compatibility_rule, repository


def test_compatibility_rule_service_seeds_defaults_dry_run_and_creates_rule() -> None:
    service = CompatibilityRuleService(repository(), AllowPolicy())

    dry_run = service.seed_default_rules(SCOPE, dry_run=True)
    created = service.create_rule(compatibility_rule("no_removed_route"))

    assert dry_run["dry_run"] is True
    assert dry_run["rule_count"] >= 1
    assert service.list_rules(SCOPE)[0].compatibility_rule_id == created.compatibility_rule_id
