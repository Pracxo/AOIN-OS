from __future__ import annotations

from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
from aion_brain.production_auth.identity_assertion_pipeline import (
    OfflineIdentityAssertionVerificationPipeline,
)
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
)
from aion_brain.production_auth.identity_assertion_replay_service import (
    IdentityAssertionReplayProtectionService,
)
from aion_brain.production_auth.identity_assertion_verifier import (
    OfflineEd25519IdentityAssertionVerifier,
)
from tests.test_identity_assertion_contracts import (
    NOW,
    make_envelope,
    make_key_pair,
    make_payload,
    make_policy,
)
from tests.test_identity_assertion_replay_contracts import memory_engine


def make_pipeline() -> tuple[OfflineIdentityAssertionVerificationPipeline, object]:
    engine = memory_engine()
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )
    return (
        OfflineIdentityAssertionVerificationPipeline(
            verifier=verifier,
            replay_protection=service,
            clock=lambda: NOW,
        ),
        signing_material,
    )


def test_pipeline_first_valid_then_repeated_assertion() -> None:
    pipeline, signing_material = make_pipeline()
    envelope = make_envelope(signing_material)

    first = pipeline.verify_once(envelope)
    second = pipeline.verify_once(envelope)

    assert first.result.outcome == "verified_once"
    assert first.result.cryptographic_verified is True
    assert first.result.verification_and_replay_checks_passed is True
    assert second.result.outcome == "replay_detected"
    assert second.result.replay_detected is True
    assert second.result.verification_and_replay_checks_passed is False


def test_pipeline_changed_payload_same_assertion_id_collides() -> None:
    pipeline, signing_material = make_pipeline()
    first = make_envelope(signing_material)
    changed = make_envelope(
        signing_material,
        make_payload(assertion_id="assertion-001", actor_id="actor-999"),
    )

    assert pipeline.verify_once(first).result.outcome == "verified_once"
    collision = pipeline.verify_once(changed)

    assert collision.result.outcome == "identifier_collision"
    assert collision.result.identifier_collision is True
    assert collision.result.fail_closed is True


def test_pipeline_crypto_rejection_skips_replay() -> None:
    pipeline, signing_material = make_pipeline()
    payload = make_payload()
    good_envelope = make_envelope(signing_material, payload)
    bad_envelope = good_envelope.model_copy(
        update={"payload": payload.model_copy(update={"subject": "tampered"})},
    )

    rejected = pipeline.verify_once(bad_envelope)

    assert rejected.result.outcome == "verification_rejected"
    assert rejected.result.cryptographic_verified is False
    assert rejected.result.replay_check_performed is False
    assert rejected.replay_bundle is None
