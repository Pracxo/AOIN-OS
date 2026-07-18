from __future__ import annotations

from datetime import timedelta

from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from aion_brain.production_auth.identity_assertion_replay_service import (
    IdentityAssertionReplayProtectionService,
)
from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import make_envelope, make_key_pair, make_payload
from tests.test_identity_assertion_replay_contracts import NOW, memory_engine, replay_fixture


class SpyRepository(IdentityAssertionReplayRepository):
    def __init__(self) -> None:
        self.claim_calls = 0

    def claim(self, record):  # type: ignore[no-untyped-def]
        self.claim_calls += 1
        raise AssertionError("claim should not be called")


def test_service_first_claim_then_replay_detection() -> None:
    fixture = replay_fixture()

    first = fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )
    second = fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )

    assert first.result.outcome == "claimed"
    assert first.result.replay_protection_passed is True
    assert first.result.fail_closed is False
    assert second.result.outcome == "replay_detected"
    assert second.result.replay_detected is True
    assert second.result.fail_closed is True


def test_service_changed_valid_payload_with_same_assertion_id_collides() -> None:
    signing_material, public_key = make_key_pair()
    first_envelope = make_envelope(signing_material)
    changed_payload = make_payload(assertion_id="assertion-001", subject="subject-999")
    changed_envelope = make_envelope(signing_material, changed_payload)
    repository = IdentityAssertionReplayRepository(engine=memory_engine(), auto_create=True)
    service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=replay_fixture().verifier.policy,
        clock=lambda: NOW,
    )

    assert service.protect(
        envelope=first_envelope,
        verification_bundle=verifier.verify(first_envelope),
    ).result.outcome == "claimed"
    collision = service.protect(
        envelope=changed_envelope,
        verification_bundle=verifier.verify(changed_envelope),
    )

    assert collision.result.outcome == "identifier_collision"
    assert collision.result.identifier_collision is True
    assert collision.result.fail_closed is True


def test_service_rejected_crypto_does_not_call_repository() -> None:
    signing_material, public_key = make_key_pair()
    payload = make_payload()
    good_envelope = make_envelope(signing_material, payload)
    bad_envelope = good_envelope.model_copy(
        update={"payload": payload.model_copy(update={"subject": "other"})},
    )
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=replay_fixture().verifier.policy,
        clock=lambda: NOW,
    )
    rejected_bundle = verifier.verify(bad_envelope)
    spy = SpyRepository()
    service = IdentityAssertionReplayProtectionService(
        repository=spy,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )

    result = service.protect(envelope=bad_envelope, verification_bundle=rejected_bundle)

    assert result.result.outcome == "verification_rejected"
    assert result.result.replay_check_performed is False
    assert spy.claim_calls == 0


def test_service_mismatch_and_expired_assertion_do_not_call_repository() -> None:
    fixture = replay_fixture()
    signing_material, _public_key = make_key_pair()
    mismatched_envelope = make_envelope(
        signing_material,
        make_payload(assertion_id="assertion-002"),
    )
    spy = SpyRepository()
    mismatch_service = IdentityAssertionReplayProtectionService(
        repository=spy,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )
    mismatch = mismatch_service.protect(
        envelope=mismatched_envelope,
        verification_bundle=fixture.verification_bundle,
    )
    expired_service = IdentityAssertionReplayProtectionService(
        repository=spy,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW + timedelta(minutes=6),
    )
    expired = expired_service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )

    assert mismatch.result.outcome == "verification_bundle_mismatch"
    assert expired.result.outcome == "assertion_expired"
    assert spy.claim_calls == 0
