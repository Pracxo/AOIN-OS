"""Explicit verified-knowledge candidate revalidation."""

from __future__ import annotations

from datetime import datetime

from aion_brain.contracts.knowledge_verified_memory import (
    VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION,
    VerifiedKnowledgeCandidateEligibilityInput,
    VerifiedKnowledgeCandidateVersion,
    VerifiedKnowledgeRevalidationRequest,
    VerifiedKnowledgeRevalidationResult,
    VerifiedKnowledgeVersionReason,
    verified_knowledge_fingerprint,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    build_verified_knowledge_candidate,
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_versioning import (
    create_candidate_version,
)


def revalidate_verified_knowledge_candidate(
    *,
    request: VerifiedKnowledgeRevalidationRequest,
    prior_candidate_version: VerifiedKnowledgeCandidateVersion,
    eligibility_input: VerifiedKnowledgeCandidateEligibilityInput,
    created_at: datetime | None = None,
) -> VerifiedKnowledgeRevalidationResult:
    """Explicitly revalidate a candidate and recompute confidence from scratch."""

    if request.candidate_version_id != prior_candidate_version.candidate_version_id:
        raise ValueError("revalidation request prior version mismatch")
    decision = evaluate_verified_knowledge_candidate_eligibility(eligibility_input)
    new_candidate = build_verified_knowledge_candidate(
        eligibility_input=eligibility_input,
        eligibility_decision=decision,
        candidate_version=prior_candidate_version.version_number + 1,
        created_at=created_at,
    )
    new_version = create_candidate_version(
        new_candidate,
        previous_version=prior_candidate_version,
        version_reason=VerifiedKnowledgeVersionReason.EXPLICIT_REVALIDATION,
        created_at=created_at,
    )
    carry_forward_blocked = any(
        trigger.value
        in {"retraction_recorded", "supersession_recorded", "evidence_removed"}
        for trigger in request.triggers
    )
    payload = {
        "schema_version": VERIFIED_KNOWLEDGE_REVALIDATION_SCHEMA_VERSION,
        "request": request,
        "prior_candidate_version": prior_candidate_version,
        "new_candidate_version": new_version,
        "eligibility_decision": decision,
        "lineage_revalidated": True,
        "confidence_recomputed_from_scratch": True,
        "carry_forward_blocked": carry_forward_blocked,
        "approval_created": False,
        "verified_knowledge_created": False,
        "persistent_write_applied": False,
        "cognitive_memory_written": False,
        "belief_mutated": False,
        "runtime_effect": False,
    }
    return VerifiedKnowledgeRevalidationResult.model_validate(
        {**payload, "result_fingerprint": verified_knowledge_fingerprint(payload)}
    )
