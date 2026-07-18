from __future__ import annotations

from tests.test_identity_assertion_replay_contracts import replay_fixture


def test_replay_evidence_excludes_raw_identity_assertion_material() -> None:
    fixture = replay_fixture()
    bundle = fixture.service.protect(
        envelope=fixture.envelope,
        verification_bundle=fixture.verification_bundle,
    )
    rendered = str(bundle.model_dump(mode="json"))

    for forbidden in (
        "issuer.aion.local",
        "assertion-001",
        fixture.envelope.signature,
        "subject-001",
        "actor-001",
        "workspace-001",
        "read:evidence",
        "offline:verify",
        "SELECT",
        "INSERT",
        "OperationalError",
        "IntegrityError",
    ):
        assert forbidden not in rendered
    assert bundle.result.raw_assertion_stored is False
    assert bundle.result.raw_signature_stored is False
    assert bundle.result.verified_claims_persisted is False
