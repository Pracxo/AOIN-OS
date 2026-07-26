"""Immutable verified-knowledge candidate versioning."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.knowledge_verified_memory import (
    VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION,
    VerifiedKnowledgeCandidate,
    VerifiedKnowledgeCandidateHistory,
    VerifiedKnowledgeCandidateVersion,
    VerifiedKnowledgeLifecycleStatus,
    VerifiedKnowledgeVersionReason,
    utc_now,
    verified_knowledge_fingerprint,
)


def _candidate_with_version(
    candidate: VerifiedKnowledgeCandidate,
    *,
    version_number: int,
    lifecycle_status: VerifiedKnowledgeLifecycleStatus,
    version_reason: VerifiedKnowledgeVersionReason,
    supersedes_candidate_version_id: str | None = None,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeCandidate:
    identity_digest = candidate.candidate_identity_id.removeprefix("candidate-identity-")
    payload = candidate.model_dump(mode="python")
    payload.update(
        {
            "candidate_id": f"candidate-{identity_digest}-v{version_number:03d}",
            "candidate_version": version_number,
            "lifecycle_status": lifecycle_status,
            "supersedes_candidate_version_id": supersedes_candidate_version_id,
            "created_at": created_at or utc_now(),
            "reason_codes": tuple(
                dict.fromkeys(
                    (
                        *candidate.reason_codes,
                        {
                            VerifiedKnowledgeVersionReason.INITIAL: (
                                "verified_candidate_version_created"
                            ),
                            VerifiedKnowledgeVersionReason.SUPERSESSION_RECORDED: (
                                "verified_candidate_supersession_recorded"
                            ),
                            VerifiedKnowledgeVersionReason.RETRACTION_RECORDED: (
                                "verified_candidate_retraction_recorded"
                            ),
                            VerifiedKnowledgeVersionReason.EXPIRY_REACHED: (
                                "verified_candidate_expiry_recorded"
                            ),
                        }.get(version_reason, "verified_candidate_version_created"),
                    )
                )
            ),
        }
    )
    payload.pop("candidate_fingerprint", None)
    return VerifiedKnowledgeCandidate.model_validate(
        {**payload, "candidate_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def create_candidate_version(
    candidate: VerifiedKnowledgeCandidate,
    *,
    previous_version: VerifiedKnowledgeCandidateVersion | None = None,
    version_reason: VerifiedKnowledgeVersionReason = VerifiedKnowledgeVersionReason.INITIAL,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeCandidateVersion:
    """Create an append-only candidate version."""

    expected_number = 1 if previous_version is None else previous_version.version_number + 1
    if candidate.candidate_version != expected_number:
        candidate = _candidate_with_version(
            candidate,
            version_number=expected_number,
            lifecycle_status=candidate.lifecycle_status,
            version_reason=version_reason,
            created_at=created_at,
        )
    version_id = f"{candidate.candidate_identity_id}-v{candidate.candidate_version:03d}"
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION,
        "candidate_version_id": version_id,
        "candidate_identity_id": candidate.candidate_identity_id,
        "candidate_id": candidate.candidate_id,
        "version_number": candidate.candidate_version,
        "version_reason": version_reason,
        "candidate": candidate,
        "previous_candidate_version_id": (
            previous_version.candidate_version_id if previous_version is not None else None
        ),
        "supersedes_candidate_version_id": candidate.supersedes_candidate_version_id,
        "created_at": created_at or candidate.created_at,
        "persistent_write_applied": False,
        "cognitive_memory_written": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeCandidateVersion.model_validate(
        {**payload, "version_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def build_candidate_history(
    versions: tuple[VerifiedKnowledgeCandidateVersion, ...],
) -> VerifiedKnowledgeCandidateHistory:
    """Build a contiguous immutable history for one candidate identity."""

    ordered = tuple(sorted(versions, key=lambda item: item.version_number))
    identity_id = ordered[0].candidate_identity_id if ordered else "candidate-identity-empty"
    latest = ordered[-1].candidate_version_id if ordered else "candidate-identity-empty-v000"
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_VERSION_SCHEMA_VERSION,
        "candidate_identity_id": identity_id,
        "versions": ordered,
        "latest_candidate_version_id": latest,
        "version_count": len(ordered),
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeCandidateHistory.model_validate(
        {**payload, "history_fingerprint": verified_knowledge_fingerprint(payload)}
    )


def supersede_candidate_version(
    version: VerifiedKnowledgeCandidateVersion,
    *,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeCandidateVersion:
    """Record supersession without deleting prior history."""

    candidate = _candidate_with_version(
        version.candidate,
        version_number=version.version_number + 1,
        lifecycle_status=VerifiedKnowledgeLifecycleStatus.SUPERSEDED,
        version_reason=VerifiedKnowledgeVersionReason.SUPERSESSION_RECORDED,
        supersedes_candidate_version_id=version.candidate_version_id,
        created_at=created_at,
    )
    return create_candidate_version(
        candidate,
        previous_version=version,
        version_reason=VerifiedKnowledgeVersionReason.SUPERSESSION_RECORDED,
        created_at=created_at,
    )


def retract_candidate_version(
    version: VerifiedKnowledgeCandidateVersion,
    *,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeCandidateVersion:
    """Record retraction without deleting prior history."""

    candidate = _candidate_with_version(
        version.candidate,
        version_number=version.version_number + 1,
        lifecycle_status=VerifiedKnowledgeLifecycleStatus.RETRACTED,
        version_reason=VerifiedKnowledgeVersionReason.RETRACTION_RECORDED,
        created_at=created_at,
    )
    return create_candidate_version(
        candidate,
        previous_version=version,
        version_reason=VerifiedKnowledgeVersionReason.RETRACTION_RECORDED,
        created_at=created_at,
    )


def expire_candidate_version(
    version: VerifiedKnowledgeCandidateVersion,
    *,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeCandidateVersion:
    """Record expiry without deleting prior history."""

    candidate = _candidate_with_version(
        version.candidate,
        version_number=version.version_number + 1,
        lifecycle_status=VerifiedKnowledgeLifecycleStatus.EXPIRED,
        version_reason=VerifiedKnowledgeVersionReason.EXPIRY_REACHED,
        created_at=created_at,
    )
    return create_candidate_version(
        candidate,
        previous_version=version,
        version_reason=VerifiedKnowledgeVersionReason.EXPIRY_REACHED,
        created_at=created_at,
    )
