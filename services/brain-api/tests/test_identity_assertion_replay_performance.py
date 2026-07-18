from __future__ import annotations

import time

from aion_brain.contracts.identity_assertion_replay import IdentityAssertionReplayPolicy
from aion_brain.production_auth.identity_assertion_pipeline import (
    OfflineIdentityAssertionVerificationPipeline,
)
from aion_brain.production_auth.identity_assertion_replay import (
    derive_identity_assertion_replay_key,
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
from tests.test_identity_assertion_replay_contracts import file_engine, make_replay_record


def test_replay_key_derivation_performance_smoke() -> None:
    start = time.monotonic()
    for index in range(1000):
        derive_identity_assertion_replay_key(
            issuer="issuer.aion.local",
            assertion_id=f"assertion-{index}",
        )
    assert time.monotonic() - start < 10


def test_repository_claim_and_duplicate_performance_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "performance.sqlite")
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    records = [make_replay_record(assertion_id=f"perf-{index}") for index in range(200)]

    start = time.monotonic()
    for record in records:
        assert repository.claim(record).outcome == "claimed"
    assert time.monotonic() - start < 30

    duplicate_start = time.monotonic()
    for record in records:
        assert repository.claim(record).outcome == "replay_detected"
    assert time.monotonic() - duplicate_start < 30


def test_pipeline_performance_smoke(tmp_path) -> None:  # type: ignore[no-untyped-def]
    engine = file_engine(tmp_path / "pipeline-performance.sqlite")
    repository = IdentityAssertionReplayRepository(engine=engine, auto_create=True)
    service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: NOW,
    )
    signing_material, public_key = make_key_pair()
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: NOW,
    )
    pipeline = OfflineIdentityAssertionVerificationPipeline(
        verifier=verifier,
        replay_protection=service,
        clock=lambda: NOW,
    )
    envelopes = [
        make_envelope(signing_material, make_payload(assertion_id=f"pipeline-{index}"))
        for index in range(100)
    ]

    start = time.monotonic()
    for envelope in envelopes:
        assert pipeline.verify_once(envelope).result.outcome == "verified_once"
        assert pipeline.verify_once(envelope).result.outcome == "replay_detected"
    assert time.monotonic() - start < 45
