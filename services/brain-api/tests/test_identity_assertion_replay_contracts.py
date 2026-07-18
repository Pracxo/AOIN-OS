from __future__ import annotations

from datetime import datetime, timedelta
from pathlib import Path
from typing import NamedTuple

import pytest
from pydantic import ValidationError
from sqlalchemy import create_engine, func, select
from sqlalchemy.engine import Engine
from sqlalchemy.pool import StaticPool

from aion_brain.contracts.identity_assertion import (
    IdentityAssertionEnvelope,
    IdentityAssertionVerificationBundle,
    assertion_fingerprint,
)
from aion_brain.contracts.identity_assertion_replay import (
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    CANDIDATE_ID,
    DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS,
    DEFAULT_CLEANUP_BATCH_SIZE,
    DEFAULT_MAXIMUM_RETENTION_SECONDS,
    DEFAULT_MINIMUM_RETENTION_SECONDS,
    IMPLEMENTATION_TASK,
    MANDATORY_RUNTIME_BOUNDARY_REASON_CODES,
    REPLAY_EVIDENCE_SCHEMA_VERSION,
    REPLAY_KEY_DOMAIN_SEPARATOR,
    REPLAY_KEY_SCHEMA_VERSION,
    REPLAY_PIPELINE_SCHEMA_VERSION,
    REPLAY_POLICY_SCHEMA_VERSION,
    REPLAY_REASON_CODE_REGISTRY_VERSION,
    REPLAY_RECORD_SCHEMA_VERSION,
    REPLAY_RESULT_SCHEMA_VERSION,
    TABLE_NAME,
    WORKSTREAM,
    IdentityAssertionReplayPolicy,
    IdentityAssertionReplayProtectionResult,
    IdentityAssertionReplayRecord,
    IdentityAssertionReplayRepositoryResult,
    protection_reason_codes,
    repository_reason_codes,
    validate_replay_reason_codes,
)
from aion_brain.production_auth.identity_assertion_replay import (
    compute_identity_assertion_retain_until,
    derive_identity_assertion_issuer_fingerprint,
    derive_identity_assertion_replay_key,
)
from aion_brain.production_auth.identity_assertion_replay_repository import (
    IdentityAssertionReplayRepository,
    aion_identity_assertion_replay_claims,
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

ROOT = Path(__file__).resolve().parents[3]


class ReplayFixture(NamedTuple):
    engine: Engine
    repository: IdentityAssertionReplayRepository
    service: IdentityAssertionReplayProtectionService
    verifier: OfflineEd25519IdentityAssertionVerifier
    envelope: IdentityAssertionEnvelope
    verification_bundle: IdentityAssertionVerificationBundle


def memory_engine() -> Engine:
    return create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )


def file_engine(path: Path) -> Engine:
    return create_engine(
        f"sqlite+pysqlite:///{path}",
        connect_args={"check_same_thread": False, "timeout": 30},
    )


def replay_fixture(
    *,
    engine: Engine | None = None,
    envelope: IdentityAssertionEnvelope | None = None,
    service_clock: datetime = NOW,
    verifier_clock: datetime = NOW,
    auto_create: bool = True,
) -> ReplayFixture:
    selected_engine = engine or memory_engine()
    repository = IdentityAssertionReplayRepository(
        engine=selected_engine,
        auto_create=auto_create,
    )
    service = IdentityAssertionReplayProtectionService(
        repository=repository,
        policy=IdentityAssertionReplayPolicy(),
        clock=lambda: service_clock,
    )
    signing_material, public_key = make_key_pair()
    selected_envelope = envelope or make_envelope(signing_material)
    verifier = OfflineEd25519IdentityAssertionVerifier(
        public_keys=(public_key,),
        policy=make_policy(),
        clock=lambda: verifier_clock,
    )
    verification_bundle = verifier.verify(selected_envelope)
    return ReplayFixture(
        engine=selected_engine,
        repository=repository,
        service=service,
        verifier=verifier,
        envelope=selected_envelope,
        verification_bundle=verification_bundle,
    )


def make_replay_record(
    *,
    assertion_id: str = "assertion-001",
    issuer: str = "issuer.aion.local",
    subject: str = "subject-001",
    claimed_at: datetime = NOW,
    assertion_expires_at: datetime | None = None,
    retain_until: datetime | None = None,
) -> IdentityAssertionReplayRecord:
    expires_at = assertion_expires_at or (claimed_at + timedelta(minutes=5))
    payload = make_payload(
        assertion_id=assertion_id,
        issuer=issuer,
        subject=subject,
        issued_at=claimed_at,
        not_before=claimed_at,
        expires_at=expires_at,
    )
    policy = IdentityAssertionReplayPolicy()
    computed_retain_until = retain_until or compute_identity_assertion_retain_until(
        claimed_at=claimed_at,
        assertion_expires_at=expires_at,
        policy=policy,
    )
    return IdentityAssertionReplayRecord(
        replay_key=derive_identity_assertion_replay_key(
            issuer=issuer,
            assertion_id=assertion_id,
        ),
        issuer_fingerprint=derive_identity_assertion_issuer_fingerprint(issuer=issuer),
        assertion_fingerprint=assertion_fingerprint(payload) or "",
        claimed_at=claimed_at,
        assertion_expires_at=expires_at,
        retain_until=computed_retain_until,
        created_at=claimed_at,
    )


def table_count(engine: Engine) -> int:
    with engine.connect() as connection:
        return int(
            connection.execute(
                select(func.count()).select_from(aion_identity_assertion_replay_claims)
            ).scalar_one()
        )


def test_replay_contract_constants_match_authorization() -> None:
    assert AUTHORIZATION_TRANSACTION_ID == "AION-163-PA-0007"
    assert IMPLEMENTATION_TASK == "AION-164"
    assert AUTHORIZATION_SCOPE == "persistent-identity-assertion-replay-protection-core"
    assert CANDIDATE_ID == "production-auth-identity-assertion-replay-protection"
    assert WORKSTREAM == "production-auth-verification-integrity"
    assert REPLAY_KEY_SCHEMA_VERSION == "identity-assertion-replay-key/v1"
    assert REPLAY_RECORD_SCHEMA_VERSION == "identity-assertion-replay-record/v1"
    assert REPLAY_POLICY_SCHEMA_VERSION == "identity-assertion-replay-policy/v1"
    assert REPLAY_RESULT_SCHEMA_VERSION == "identity-assertion-replay-result/v1"
    assert REPLAY_EVIDENCE_SCHEMA_VERSION == "identity-assertion-replay-evidence/v1"
    assert REPLAY_PIPELINE_SCHEMA_VERSION == "identity-assertion-replay-pipeline/v1"
    assert REPLAY_REASON_CODE_REGISTRY_VERSION == "identity-assertion-replay-reason-codes/v1"
    assert REPLAY_KEY_DOMAIN_SEPARATOR == b"AION-IDENTITY-ASSERTION-REPLAY-V1\0"
    assert DEFAULT_MINIMUM_RETENTION_SECONDS == 86400
    assert DEFAULT_MAXIMUM_RETENTION_SECONDS == 604800
    assert DEFAULT_CLEANUP_BATCH_SIZE == 1000
    assert DEFAULT_ALLOWED_CLOCK_SKEW_SECONDS == 30
    assert TABLE_NAME == "aion_identity_assertion_replay_claims"


def test_record_is_immutable_and_rejects_raw_fields() -> None:
    record = make_replay_record()
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(**record.model_dump(), issuer="issuer.aion.local")
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(**record.model_dump(), assertion_id="assertion-001")
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(**record.model_dump(), signature="hidden")
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(**record.model_dump(), metadata={})
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(
            **{**record.model_dump(), "replay_key": "A" * 64},
        )
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(
            **{**record.model_dump(), "claimed_at": datetime(2026, 7, 18, 12, 0)},
        )
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRecord(
            **{
                **record.model_dump(),
                "created_at": record.claimed_at + timedelta(seconds=1),
            },
        )
    with pytest.raises(ValidationError):
        record.replay_key = "0" * 64  # type: ignore[misc]


def test_repository_and_protection_results_enforce_outcome_invariants() -> None:
    record = make_replay_record()
    claimed = IdentityAssertionReplayRepositoryResult(
        operation_id="op-1",
        outcome="claimed",
        claim_created=True,
        replay_detected=False,
        identifier_collision=False,
        repository_available=True,
        schema_available=True,
        fail_closed=False,
        existing_assertion_fingerprint_matches=False,
        record=record,
        primary_reason_code=repository_reason_codes("claimed")[0],
        reason_codes=repository_reason_codes("claimed"),
        created_at=NOW,
    )
    assert claimed.record == record
    with pytest.raises(ValidationError):
        IdentityAssertionReplayRepositoryResult(
            **{**claimed.model_dump(), "fail_closed": True, "fingerprint": None},
        )
    protection = IdentityAssertionReplayProtectionResult(
        replay_protection_id="replay-1",
        outcome="claimed",
        cryptographic_verification_verified=True,
        replay_check_performed=True,
        replay_protection_passed=True,
        claim_created=True,
        replay_detected=False,
        identifier_collision=False,
        repository_available=True,
        schema_available=True,
        fail_closed=False,
        replay_key=record.replay_key,
        issuer_fingerprint=record.issuer_fingerprint,
        assertion_fingerprint=record.assertion_fingerprint,
        retain_until=record.retain_until,
        primary_reason_code=protection_reason_codes("claimed")[0],
        reason_codes=protection_reason_codes("claimed"),
        checked_at=NOW,
    )
    assert protection.request_authenticated is False
    assert protection.runtime_effect is False
    with pytest.raises(ValidationError):
        IdentityAssertionReplayProtectionResult(
            **{
                **protection.model_dump(),
                "runtime_effect": True,
                "fingerprint": None,
            },
        )


def test_reason_codes_are_strict_and_include_runtime_boundary_codes() -> None:
    valid = protection_reason_codes("claimed")
    assert all(code in valid for code in MANDATORY_RUNTIME_BOUNDARY_REASON_CODES)
    assert validate_replay_reason_codes(valid) == valid
    with pytest.raises(ValueError, match="duplicate"):
        validate_replay_reason_codes(valid + (valid[0],))
    with pytest.raises(ValueError, match="unknown"):
        validate_replay_reason_codes(("unknown", *MANDATORY_RUNTIME_BOUNDARY_REASON_CODES))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="mandatory"):
        validate_replay_reason_codes(("identity_assertion_replay_claimed",))
