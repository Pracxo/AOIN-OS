"""AION-178 shadow evidence tests."""

from __future__ import annotations

from test_self_improvement_shadow_contracts import make_bundle

from aion_brain.contracts.self_improvement_shadow import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    fingerprint_model,
)


def test_evidence_bundle_contains_lineage_audit_provenance_and_diagnostics() -> None:
    bundle = make_bundle()

    assert bundle.authorization_transaction_id == AUTHORIZATION_TRANSACTION_ID
    assert bundle.authorization_scope == AUTHORIZATION_SCOPE
    assert bundle.audit_events[0].redacted is True
    assert bundle.provenance is not None
    assert bundle.provenance.runtime_effect is False
    assert bundle.diagnostics.shadow_mode_implemented is True
    assert bundle.diagnostics.shadow_mode_runtime_enabled is False
    assert bundle.diagnostics.network_calls == 0
    assert bundle.diagnostics.git_operations == 0
    assert bundle.diagnostics.real_pull_requests == 0
    assert bundle.diagnostics.runtime_promotions == 0


def test_evidence_fingerprint_is_deterministic_and_safety_relevant() -> None:
    bundle = make_bundle()
    changed = bundle.model_copy(update={"reason_codes": ("shadow_run_completed_without_pattern",)})

    assert fingerprint_model(bundle) == bundle.fingerprint
    assert fingerprint_model(changed) != bundle.fingerprint


def test_evidence_exposes_no_runtime_actions() -> None:
    bundle = make_bundle()

    assert bundle.implementation_authorization_created is False
    assert bundle.approval_created is False
    assert bundle.source_modified is False
    assert bundle.git_mutated is False
    assert bundle.pull_request_created is False
    assert bundle.merged is False
    assert bundle.active_learning_promoted is False
    assert bundle.runtime_effect is False
