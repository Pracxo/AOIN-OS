"""In-memory shadow adaptation composition for AION-228."""

from __future__ import annotations

from aion_brain.contracts.governed_continual_learning import (
    ContinualLearningShadowBinding,
    ContinualLearningShadowStatus,
    build_record,
    continual_fingerprint,
    utc_now,
)
from aion_brain.governed_learning_memory.engagement_shadow_application import (
    ControlledEngagementShadowApplicationService,
)


class ControlledContinualLearningShadowAdapter:
    """AION-228 binding layer over the existing in-memory shadow service."""

    component_service = ControlledEngagementShadowApplicationService

    def build_shadow_binding(
        self,
        *,
        session_id: str,
        cycle_id: str,
        adaptation_identity_id: str,
        candidate_fingerprint: str,
        approval_bundle_fingerprint: str,
        counterfactual_case_count: int,
    ) -> ContinualLearningShadowBinding:
        """Record an approved in-memory shadow adaptation with zero active overlays."""

        counterfactuals = tuple(
            continual_fingerprint({"case": index, "adaptation": adaptation_identity_id})
            for index in range(counterfactual_case_count)
        )
        return build_record(
            ContinualLearningShadowBinding,
            {
                "schema_version": "aion-glm-continual-learning-shadow-binding/v1",
                "binding_id": f"{cycle_id}-shadow-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "status": ContinualLearningShadowStatus.SHADOW_APPLIED,
                "adaptation_identity_id": adaptation_identity_id,
                "candidate_fingerprint": candidate_fingerprint,
                "approval_bundle_fingerprint": approval_bundle_fingerprint,
                "overlay_fingerprint": continual_fingerprint({"overlay": adaptation_identity_id}),
                "baseline_fingerprint": continual_fingerprint({"baseline": cycle_id}),
                "counterfactual_result_fingerprints": counterfactuals,
                "recommendation_fingerprint": continual_fingerprint(
                    {"recommendation": adaptation_identity_id, "bounded": True}
                ),
                "approval_count": 1,
                "active_overlay_records_after_cycle": 0,
                "created_at": utc_now(),
            },
            "shadow_binding_fingerprint",
        )

    def build_noop_shadow_binding(
        self,
        *,
        session_id: str,
        cycle_id: str,
    ) -> ContinualLearningShadowBinding:
        """Record an explicit no-op or baseline-retained shadow binding."""

        return build_record(
            ContinualLearningShadowBinding,
            {
                "schema_version": "aion-glm-continual-learning-shadow-binding/v1",
                "binding_id": f"{cycle_id}-shadow-binding",
                "session_id": session_id,
                "cycle_id": cycle_id,
                "status": ContinualLearningShadowStatus.BASELINE_RETAINED,
                "adaptation_identity_id": f"{cycle_id}-baseline",
                "candidate_fingerprint": continual_fingerprint({"candidate": "not_applicable"}),
                "approval_bundle_fingerprint": continual_fingerprint(
                    {"approval": "not_applicable"}
                ),
                "overlay_fingerprint": continual_fingerprint({"overlay": "none"}),
                "baseline_fingerprint": continual_fingerprint({"baseline": cycle_id}),
                "counterfactual_result_fingerprints": (),
                "recommendation_fingerprint": continual_fingerprint({"recommendation": "baseline"}),
                "approval_count": 0,
                "active_overlay_records_after_cycle": 0,
                "created_at": utc_now(),
            },
            "shadow_binding_fingerprint",
        )
