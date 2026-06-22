"""Preference learning candidate service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from aion_brain.contracts.preferences import PreferenceLearningCandidate, PreferenceRecord
from aion_brain.instructions.preferences import PreferenceService
from aion_brain.instructions.repository import InstructionRepository
from aion_brain.instructions.service import _authorize, _emit, _ensure_enabled


class PreferenceLearningService:
    """Create reviewable preference candidates only from explicit signals."""

    def __init__(
        self,
        repository: InstructionRepository,
        policy_adapter: object | None,
        *,
        preference_service: PreferenceService,
        telemetry_service: object | None = None,
        settings: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._preference_service = preference_service
        self._telemetry_service = telemetry_service
        self._settings = settings

    def propose_candidate(
        self,
        candidate: PreferenceLearningCandidate,
    ) -> PreferenceLearningCandidate:
        _ensure_enabled(
            self._settings,
            "preference_learning_enabled",
            "preference_learning_disabled",
        )
        _authorize(
            self._policy_adapter,
            "preference.candidate.create",
            "preference_candidate",
            candidate.candidate_id,
            candidate.owner_scope,
            trace_id=candidate.trace_id,
            actor_id=candidate.actor_id,
            workspace_id=candidate.workspace_id,
            risk_level="low",
        )
        stored = self._repository.save_candidate(
            candidate.model_copy(update={"created_at": candidate.created_at or datetime.now(UTC)})
        )
        _emit(
            self._telemetry_service,
            event_type="preference_candidate_created",
            node_type="candidate",
            node_id=stored.candidate_id,
            trace_id=stored.trace_id,
            intensity=0.5,
            payload={"preference_key": stored.preference_key, "owner_scope": stored.owner_scope},
        )
        return stored

    def propose_from_dialogue(
        self,
        dialogue_payload: dict[str, Any],
        *,
        explicit: bool,
        owner_scope: list[str],
    ) -> PreferenceLearningCandidate | None:
        if not explicit:
            return None
        key = str(dialogue_payload.get("preference_key") or "interaction.response_style")
        value = dialogue_payload.get("preference_value")
        if not isinstance(value, dict):
            value = {"value": str(dialogue_payload.get("preference_value") or "concise")}
        candidate = PreferenceLearningCandidate(
            candidate_id=str(
                dialogue_payload.get("candidate_id") or "preference-candidate-dialogue"
            ),
            trace_id=_optional_str(dialogue_payload.get("trace_id")),
            actor_id=_optional_str(dialogue_payload.get("actor_id")),
            workspace_id=_optional_str(dialogue_payload.get("workspace_id")),
            preference_type="style",
            preference_key=key,
            proposed_value=value,
            confidence=float(dialogue_payload.get("confidence") or 0.5),
            owner_scope=owner_scope,
            source_refs=[str(dialogue_payload.get("message_id"))]
            if dialogue_payload.get("message_id")
            else [],
            reason="Explicit dialogue preference request.",
            metadata={"source": "dialogue"},
            created_by=_optional_str(dialogue_payload.get("actor_id")),
        )
        return self.propose_candidate(candidate)

    def propose_from_feedback(
        self,
        feedback_payload: dict[str, Any],
        *,
        explicit: bool,
        owner_scope: list[str],
    ) -> PreferenceLearningCandidate | None:
        if not explicit:
            return None
        value = feedback_payload.get("preference_value")
        if not isinstance(value, dict):
            value = {"feedback": str(feedback_payload.get("feedback_type") or "generic")}
        candidate = PreferenceLearningCandidate(
            candidate_id=str(
                feedback_payload.get("candidate_id") or "preference-candidate-feedback"
            ),
            trace_id=_optional_str(feedback_payload.get("trace_id")),
            actor_id=_optional_str(feedback_payload.get("actor_id")),
            workspace_id=_optional_str(feedback_payload.get("workspace_id")),
            preference_type="interaction",
            preference_key=str(feedback_payload.get("preference_key") or "interaction.feedback"),
            proposed_value=value,
            confidence=float(feedback_payload.get("confidence") or 0.5),
            owner_scope=owner_scope,
            source_refs=[str(feedback_payload.get("feedback_id"))]
            if feedback_payload.get("feedback_id")
            else [],
            reason="Explicit feedback preference request.",
            metadata={"source": "feedback"},
            created_by=_optional_str(feedback_payload.get("actor_id")),
        )
        return self.propose_candidate(candidate)

    def list_candidates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        preference_type: str | None = None,
        limit: int = 100,
    ) -> list[PreferenceLearningCandidate]:
        _authorize(
            self._policy_adapter,
            "preference.candidate.read",
            "preference_candidate",
            None,
            scope,
        )
        return self._repository.list_candidates(
            scope=scope,
            status=status,
            preference_type=preference_type,
            limit=limit,
        )

    def confirm_candidate(
        self,
        candidate_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> PreferenceRecord:
        candidate = self._repository.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError("preference_candidate_not_found")
        _authorize(
            self._policy_adapter,
            "preference.candidate.update",
            "preference_candidate",
            candidate_id,
            candidate.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"status": "confirmed", "reason": reason},
        )
        now = datetime.now(UTC)
        self._repository.save_candidate(
            candidate.model_copy(update={"status": "confirmed", "resolved_at": now})
        )
        preference = self._preference_service.create_preference(
            PreferenceRecord(
                preference_id=f"preference-from-{candidate.candidate_id}",
                trace_id=candidate.trace_id,
                actor_id=candidate.actor_id,
                workspace_id=candidate.workspace_id,
                preference_type=candidate.preference_type,
                preference_key=candidate.preference_key,
                preference_value=candidate.preference_value,
                confidence=candidate.confidence,
                status="confirmed",
                owner_scope=candidate.owner_scope,
                evidence_refs=candidate.evidence_refs,
                source_refs=[*candidate.source_refs, candidate.candidate_id],
                metadata={"candidate_id": candidate.candidate_id, "resolution_reason": reason},
                created_by=actor_id or candidate.created_by,
            )
        )
        _emit(
            self._telemetry_service,
            event_type="preference_candidate_confirmed",
            node_type="candidate",
            node_id=candidate.candidate_id,
            trace_id=candidate.trace_id,
            intensity=0.7,
            payload={"preference_id": preference.preference_id},
        )
        return preference

    def reject_candidate(
        self,
        candidate_id: str,
        *,
        actor_id: str | None = None,
        reason: str | None = None,
    ) -> PreferenceLearningCandidate:
        candidate = self._repository.get_candidate(candidate_id)
        if candidate is None:
            raise ValueError("preference_candidate_not_found")
        _authorize(
            self._policy_adapter,
            "preference.candidate.update",
            "preference_candidate",
            candidate_id,
            candidate.owner_scope,
            actor_id=actor_id,
            risk_level="low",
            context={"status": "rejected", "reason": reason},
        )
        return self._repository.save_candidate(
            candidate.model_copy(
                update={
                    "status": "rejected",
                    "resolved_at": datetime.now(UTC),
                    "metadata": {**candidate.metadata, "rejection_reason": reason},
                }
            )
        )


def _optional_str(value: object) -> str | None:
    if value is None:
        return None
    text = str(value)
    return text if text else None


__all__ = ["PreferenceLearningService"]
