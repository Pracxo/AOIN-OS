"""Verified-knowledge composition helpers for AION-228."""

from __future__ import annotations

from decimal import Decimal

from aion_brain.contracts.governed_continual_learning import (
    ContinualLearningKnowledgeCandidateBinding,
    ContinualLearningKnowledgeStatus,
    ContinualLearningResearchBinding,
    build_record,
    continual_fingerprint,
    utc_now,
)
from aion_brain.knowledge_intelligence.verified_knowledge_candidates import (
    build_verified_knowledge_candidate,
    evaluate_verified_knowledge_candidate_eligibility,
)
from aion_brain.knowledge_intelligence.verified_knowledge_lineage import (
    audit_integrated_knowledge_lineage,
    build_integrated_knowledge_lineage,
)


class ControlledContinualLearningKnowledgePipeline:
    """Small AION-228 binding layer over the existing verified-candidate plane."""

    component_symbols = (
        build_integrated_knowledge_lineage,
        audit_integrated_knowledge_lineage,
        evaluate_verified_knowledge_candidate_eligibility,
        build_verified_knowledge_candidate,
    )

    def build_candidate_binding(
        self,
        *,
        session_id: str,
        cycle_id: str,
        candidate_id: str,
        research_binding: ContinualLearningResearchBinding,
        eligible: bool,
        confidence_cap: Decimal = Decimal("0.850000"),
    ) -> ContinualLearningKnowledgeCandidateBinding:
        """Build a redacted verified-candidate composition binding."""

        status = (
            ContinualLearningKnowledgeStatus.ELIGIBLE_FOR_REVIEW
            if eligible
            else ContinualLearningKnowledgeStatus.ABSTAINED
        )
        complete = Decimal("1.000000") if eligible else Decimal("0.000000")
        return build_record(
            ContinualLearningKnowledgeCandidateBinding,
            {
                "schema_version": "aion-glm-continual-learning-knowledge-binding/v1",
                "binding_id": f"{cycle_id}-candidate-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "candidate_id": candidate_id,
                "candidate_status": status,
                "candidate_fingerprint": continual_fingerprint(
                    {
                        "candidate": candidate_id,
                        "research": research_binding.research_binding_fingerprint,
                    }
                ),
                "lineage_fingerprint": continual_fingerprint(
                    {"lineage": research_binding.research_binding_fingerprint}
                ),
                "provenance_complete": complete,
                "citation_coverage": complete,
                "evidence_coverage": complete,
                "candidate_confidence_cap": confidence_cap if eligible else Decimal("0.000000"),
                "created_at": utc_now(),
            },
            "candidate_binding_fingerprint",
        )
