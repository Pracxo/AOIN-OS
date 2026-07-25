"""Correction, retraction, supersession, and contradiction evaluation."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from aion_brain.contracts.knowledge_claim_graph import (
    ClaimRelationEdge,
    ClaimRelationType,
    StructuralConflictCandidate,
)
from aion_brain.contracts.knowledge_epistemic_assessment import ContradictionStatus


@dataclass(frozen=True)
class RelationAssessment:
    """Relation posture for one target claim."""

    correction_relation_ids: tuple[str, ...]
    retraction_relation_ids: tuple[str, ...]
    supersession_relation_ids: tuple[str, ...]
    structural_conflict_candidate_ids: tuple[str, ...]
    contradiction_status: ContradictionStatus
    reason_codes: tuple[str, ...]


def assess_claim_relations(
    *,
    claim_id: str,
    relations: Iterable[ClaimRelationEdge],
    structural_conflicts: Iterable[StructuralConflictCandidate],
    independent_opposition_count: int,
) -> RelationAssessment:
    """Evaluate relations without resolving any contradiction."""

    correction_ids: list[str] = []
    retraction_ids: list[str] = []
    supersession_ids: list[str] = []
    reason_codes: list[str] = []
    for relation in sorted(relations, key=lambda item: item.relation_id):
        if relation.target_claim_id != claim_id:
            continue
        if relation.relation_type == ClaimRelationType.CORRECTS:
            correction_ids.append(relation.relation_id)
            reason_codes.append("epistemic_correction_relation_present")
        elif relation.relation_type == ClaimRelationType.RETRACTS:
            retraction_ids.append(relation.relation_id)
            reason_codes.append("epistemic_retraction_relation_present")
        elif relation.relation_type == ClaimRelationType.SUPERSEDES:
            supersession_ids.append(relation.relation_id)
            reason_codes.append("epistemic_supersession_relation_present")

    conflict_ids = tuple(
        candidate.candidate_id
        for candidate in sorted(structural_conflicts, key=lambda item: item.candidate_id)
        if claim_id in {candidate.left_claim_id, candidate.right_claim_id}
    )
    if conflict_ids or independent_opposition_count >= 2:
        contradiction_status = ContradictionStatus.MATERIAL
        reason_codes.append("epistemic_structural_conflict_material")
    elif independent_opposition_count == 1:
        contradiction_status = ContradictionStatus.UNRESOLVED
        reason_codes.append("epistemic_structural_conflict_unresolved")
    elif independent_opposition_count == 0:
        contradiction_status = ContradictionStatus.NONE_DETECTED
        reason_codes.append("epistemic_structural_conflict_none")
    else:
        contradiction_status = ContradictionStatus.INSUFFICIENT_EVIDENCE

    return RelationAssessment(
        correction_relation_ids=tuple(correction_ids),
        retraction_relation_ids=tuple(retraction_ids),
        supersession_relation_ids=tuple(supersession_ids),
        structural_conflict_candidate_ids=conflict_ids,
        contradiction_status=contradiction_status,
        reason_codes=tuple(dict.fromkeys(reason_codes)),
    )


__all__ = ["RelationAssessment", "assess_claim_relations"]
