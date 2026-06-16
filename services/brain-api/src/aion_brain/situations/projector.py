"""Deterministic situation projection engine."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.situations import (
    SituationCreateRequest,
    SituationProjectionRequest,
    SituationProjectionResult,
    SituationProjectionStatus,
    SituationRecord,
)
from aion_brain.contracts.temporal_state import StateAtom, StateAtomCreateRequest
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.situations.normalizer import SituationNormalizer
from aion_brain.situations.repository import SituationRepository
from aion_brain.situations.service import SituationService
from aion_brain.situations.state_atoms import StateAtomService
from aion_brain.situations.transitions import StateTransitionDetector


class SituationProjector:
    """Project generic local Brain records into current state atoms."""

    def __init__(
        self,
        repository: SituationRepository,
        policy_adapter: object,
        *,
        situation_service: SituationService,
        state_atom_service: StateAtomService,
        normalizer: SituationNormalizer | None = None,
        transition_detector: StateTransitionDetector | None = None,
        autonomy_governor: object | None = None,
        telemetry_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._situation_service = situation_service
        self._state_atom_service = state_atom_service
        self._normalizer = normalizer or SituationNormalizer()
        self._transition_detector = transition_detector or StateTransitionDetector()
        self._autonomy_governor = autonomy_governor
        self._telemetry_service = telemetry_service

    def project(self, request: SituationProjectionRequest) -> SituationProjectionResult:
        run_id = request.projection_run_id or f"situation-projection-{uuid4().hex}"
        now = datetime.now(UTC)
        try:
            authorize(
                self._policy_adapter,
                action_type="situation.project",
                resource_type="situation_projection",
                resource_id=run_id,
                scope=request.owner_scope,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                risk_level="medium",
                context={"mode": request.mode},
            )
        except PermissionError as exc:
            return _blocked_result(request, run_id, "blocked_by_policy", str(exc), now)
        if request.mode == "controlled" and not _autonomy_allows(self._autonomy_governor):
            return _blocked_result(
                request,
                run_id,
                "blocked_by_autonomy",
                "autonomy_denied",
                now,
            )
        emit_telemetry(
            self._telemetry_service,
            event_type="situation_projection_started",
            node_type="situation",
            node_id=run_id,
            intensity=0.5,
            trace_id=request.trace_id,
            payload={"mode": request.mode, "owner_scope": request.owner_scope},
        )
        situation_request = SituationCreateRequest(
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            situation_type="general",
            title="Current situation",
            summary=_summary(request),
            owner_scope=request.owner_scope,
            confidence=0.5 if not request.source_refs else 0.7,
            metadata={"projection_run_id": run_id, "source_count": len(request.source_refs)},
            created_by=request.actor_id,
        )
        atom_requests = self._normalizer.normalize_sources(
            source_refs=request.source_refs,
            owner_scope=request.owner_scope,
            trace_id=request.trace_id,
            observed_at=now,
        )[: request.max_state_atoms]
        if not atom_requests:
            atom_requests = [_default_atom_request(request, now)]
        if request.mode == "dry_run":
            situation = _situation_from_request(situation_request, run_id, now)
            dry_run_atoms = [
                _atom_from_request(atom, situation.situation_id, now) for atom in atom_requests
            ]
            transitions = []
            for atom in dry_run_atoms:
                previous = _previous_for_atom(self._repository, atom, request.owner_scope)
                transitions.extend(self._transition_detector.detect(previous, atom))
            return SituationProjectionResult(
                projection_run_id=run_id,
                trace_id=request.trace_id,
                actor_id=request.actor_id,
                workspace_id=request.workspace_id,
                status="dry_run",
                mode=request.mode,
                owner_scope=request.owner_scope,
                input=request.model_dump(mode="json"),
                situation_ids=[situation.situation_id],
                state_atom_ids=[atom.state_atom_id for atom in dry_run_atoms],
                transition_ids=[item.state_transition_id for item in transitions],
                situations=[situation],
                state_atoms=dry_run_atoms,
                transitions=transitions,
                warnings=["dry_run_no_persistence"],
                result={"source_count": len(request.source_refs)},
                created_by=request.actor_id,
                created_at=now,
                completed_at=datetime.now(UTC),
            )
        situation = self._situation_service.create(situation_request)
        atoms: list[StateAtom] = []
        transitions = []
        for atom_request in atom_requests:
            atom = self._state_atom_service.create(
                atom_request.model_copy(update={"situation_id": situation.situation_id})
            )
            atoms.append(atom)
            previous = _previous_for_atom(self._repository, atom, request.owner_scope)
            detected = self._transition_detector.detect(previous, atom)
            transitions.extend(detected)
            for transition in detected:
                self._repository.save_transition(transition)
                emit_telemetry(
                    self._telemetry_service,
                    event_type="state_transition_detected",
                    node_type="state_transition",
                    node_id=transition.state_transition_id,
                    intensity=0.6,
                    trace_id=transition.trace_id,
                    payload={"transition_type": transition.transition_type},
                )
        result = SituationProjectionResult(
            projection_run_id=run_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            status="completed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            input=request.model_dump(mode="json"),
            situation_ids=[situation.situation_id],
            state_atom_ids=[atom.state_atom_id for atom in atoms],
            transition_ids=[item.state_transition_id for item in transitions],
            situations=[situation],
            state_atoms=atoms,
            transitions=transitions,
            warnings=[],
            result={"source_count": len(request.source_refs)},
            created_by=request.actor_id,
            created_at=now,
            completed_at=datetime.now(UTC),
        )
        stored = self._repository.save_projection_run(result)
        emit_telemetry(
            self._telemetry_service,
            event_type="situation_projection_completed",
            node_type="situation",
            node_id=stored.projection_run_id,
            intensity=0.7,
            trace_id=stored.trace_id,
            payload={"status": stored.status, "state_atom_count": len(stored.state_atom_ids)},
        )
        return stored

    def get_projection_run(self, projection_run_id: str) -> SituationProjectionResult | None:
        return self._repository.get_projection_run(projection_run_id)

    def list_failed_runs(self, limit: int = 100) -> list[SituationProjectionResult]:
        return self._repository.list_projection_runs(status="failed", limit=limit)


def _summary(request: SituationProjectionRequest) -> str:
    if request.source_refs:
        return f"Deterministic projection over {len(request.source_refs)} source references."
    return "Deterministic projection over the configured temporal window."


def _default_atom_request(
    request: SituationProjectionRequest,
    now: datetime,
) -> StateAtomCreateRequest:
    return StateAtomCreateRequest(
        trace_id=request.trace_id,
        atom_type="system_state",
        source_type="system",
        source_id=request.projection_run_id or "projection-window",
        subject_ref="situation_projection",
        predicate="window_projected",
        value={"mode": request.mode, "source_count": len(request.source_refs)},
        status="current",
        confidence=0.5,
        sensitivity="internal",
        observed_at=now,
        owner_scope=request.owner_scope,
        metadata={"projection_source": "default_window"},
    )


def _previous_for_atom(
    repository: SituationRepository,
    atom: StateAtom,
    scope: list[str],
) -> StateAtom | None:
    candidates = repository.list_state_atoms(
        scope=scope,
        source_type=atom.source_type,
        source_id=atom.source_id,
        statuses=["current", "previous", "stale", "contradicted"],
        limit=10,
    )
    for candidate in candidates:
        if candidate.state_atom_id != atom.state_atom_id and candidate.predicate == atom.predicate:
            return candidate
    return None


def _situation_from_request(
    request: SituationCreateRequest,
    run_id: str,
    now: datetime,
) -> SituationRecord:
    return SituationRecord(
        situation_id=request.situation_id or f"situation-{run_id}",
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        status="active",
        situation_type=request.situation_type,
        title=request.title,
        summary=request.summary,
        owner_scope=request.owner_scope,
        active_goal_ids=request.active_goal_ids,
        active_task_ids=request.active_task_ids,
        active_workflow_run_ids=request.active_workflow_run_ids,
        active_focus_session_ids=request.active_focus_session_ids,
        entity_refs=request.entity_refs,
        belief_refs=request.belief_refs,
        evidence_refs=request.evidence_refs,
        memory_refs=request.memory_refs,
        constraints=request.constraints,
        confidence=request.confidence,
        metadata=request.metadata,
        created_by=request.created_by,
        created_at=now,
        updated_at=now,
        closed_at=None,
    )


def _atom_from_request(
    request: StateAtomCreateRequest,
    situation_id: str,
    now: datetime,
) -> StateAtom:
    return StateAtom(
        state_atom_id=request.state_atom_id or f"state-atom-{uuid4().hex}",
        situation_id=situation_id,
        trace_id=request.trace_id,
        atom_type=request.atom_type,
        source_type=request.source_type,
        source_id=request.source_id,
        subject_ref=request.subject_ref,
        predicate=request.predicate,
        object_ref=request.object_ref,
        value=request.value,
        status=request.status,
        confidence=request.confidence,
        sensitivity=request.sensitivity,
        observed_at=request.observed_at or now,
        valid_from=request.valid_from,
        valid_to=request.valid_to,
        owner_scope=request.owner_scope,
        evidence_refs=request.evidence_refs,
        belief_refs=request.belief_refs,
        entity_refs=request.entity_refs,
        metadata=request.metadata,
        created_at=now,
        superseded_at=None,
        deleted_at=None,
    )


def _blocked_result(
    request: SituationProjectionRequest,
    run_id: str,
    status: SituationProjectionStatus,
    reason: str,
    now: datetime,
) -> SituationProjectionResult:
    return SituationProjectionResult(
        projection_run_id=run_id,
        trace_id=request.trace_id,
        actor_id=request.actor_id,
        workspace_id=request.workspace_id,
        status=status,
        mode=request.mode,
        owner_scope=request.owner_scope,
        input=request.model_dump(mode="json"),
        situation_ids=[],
        state_atom_ids=[],
        transition_ids=[],
        warnings=[reason],
        result={"blocked_reason": reason},
        created_by=request.actor_id,
        created_at=now,
        completed_at=datetime.now(UTC),
    )


def _autonomy_allows(autonomy_governor: object | None) -> bool:
    if autonomy_governor is None:
        return True
    method = getattr(autonomy_governor, "allows", None)
    if not callable(method):
        return True
    try:
        return bool(method("situation.project"))
    except Exception:
        return False
