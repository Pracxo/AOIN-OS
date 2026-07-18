from __future__ import annotations

from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayProtectionResult
from tests.test_identity_assertion_replay_contracts import replay_fixture


def test_replay_evidence_contains_safe_fingerprints() -> None:
    fixture = replay_fixture()
    bundle = fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )

    assert bundle.result.replay_key is not None
    assert bundle.result.issuer_fingerprint is not None
    assert bundle.result.assertion_fingerprint is not None
    assert bundle.audit_event.replay_key == bundle.result.replay_key
    assert bundle.provenance.atomic_insert is True
    assert bundle.diagnostic_snapshot.table_name == "aion_identity_assertion_replay_claims"
    assert bundle.fingerprint is not None


def test_evidence_fingerprints_are_deterministic_and_safety_relevant() -> None:
    fixture = replay_fixture()
    bundle = fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )
    payload = bundle.result.model_dump(mode="python", exclude={"fingerprint"})
    same = IdentityAssertionReplayProtectionResult(**payload)
    changed = IdentityAssertionReplayProtectionResult(
        **{**payload, "replay_key": "a" * 64},
    )

    assert same.fingerprint == bundle.result.fingerprint
    assert changed.fingerprint != bundle.result.fingerprint
