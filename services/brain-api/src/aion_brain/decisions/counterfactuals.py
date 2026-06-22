"""Deterministic counterfactual simulator."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.counterfactuals import CounterfactualRun, CounterfactualRunRequest
from aion_brain.contracts.decisions import DecisionFrame, DecisionOption
from aion_brain.contracts.effects import ExpectedEffectCreateRequest
from aion_brain.decisions._shared import authorize, call_optional, emit_telemetry
from aion_brain.decisions.repository import DecisionRepository


class CounterfactualSimulator:
    """Project declared generic effects without mutating source records."""

    def __init__(
        self,
        repository: DecisionRepository,
        policy_adapter: object,
        *,
        autonomy_governor: object | None = None,
        state_atom_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        expected_effect_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._autonomy_governor = autonomy_governor
        self._state_atom_service = state_atom_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._expected_effect_service = expected_effect_service

    def run(self, request: CounterfactualRunRequest) -> CounterfactualRun:
        frame = self._repository.get_frame(request.decision_frame_id)
        if frame is None:
            raise ValueError("decision_frame_not_found")
        option = (
            self._repository.get_option(request.decision_option_id)
            if request.decision_option_id
            else None
        )
        try:
            authorize(
                self._policy_adapter,
                action_type="decision.counterfactual.run",
                resource_type="counterfactual",
                resource_id=request.counterfactual_run_id,
                scope=request.owner_scope,
                trace_id=request.trace_id or frame.trace_id,
                actor_id=frame.actor_id,
                workspace_id=frame.workspace_id,
                risk_level="medium",
                context={"mode": request.mode},
            )
        except PermissionError:
            return self._blocked_run(request, frame, option, "blocked_by_policy")
        if not _autonomy_allows(self._autonomy_governor):
            return self._blocked_run(request, frame, option, "blocked_by_autonomy")
        return self._build_run(request, frame, option)

    def simulate_option(
        self,
        frame: DecisionFrame,
        option: DecisionOption,
        input_state: dict[str, object],
    ) -> CounterfactualRun:
        return self._build_run(
            CounterfactualRunRequest(
                decision_frame_id=frame.decision_frame_id,
                decision_option_id=option.decision_option_id,
                trace_id=frame.trace_id,
                owner_scope=frame.owner_scope,
                input_state=dict(input_state),
                mode="dry_run",
            ),
            frame,
            option,
        )

    def get(self, counterfactual_run_id: str) -> CounterfactualRun | None:
        return self._repository.get_counterfactual(counterfactual_run_id)

    def _create_expected_effects(self, run: CounterfactualRun) -> None:
        create = getattr(self._expected_effect_service, "create_expected_effect", None)
        if not callable(create):
            return
        for raw in run.projected_changes:
            if not isinstance(raw, dict):
                continue
            create(
                ExpectedEffectCreateRequest(
                    expected_effect_id=_str_or_none(raw.get("expected_effect_id")),
                    trace_id=run.trace_id,
                    source_type="counterfactual",
                    source_id=run.counterfactual_run_id,
                    effect_type=str(raw.get("effect_type") or "generic"),  # type: ignore[arg-type]
                    subject_ref=_str_or_none(raw.get("subject_ref")),
                    predicate=str(raw.get("predicate") or "projected_change"),
                    object_ref=_str_or_none(raw.get("object_ref")),
                    expected_value=_dict_or_empty(raw.get("expected_value")),
                    success_criteria=_dict_or_empty(raw.get("success_criteria"))
                    or {"exists": True},
                    required=bool(raw.get("required", True)),
                    confidence=_clamp(float(raw.get("confidence", 0.5))),
                    owner_scope=run.owner_scope,
                    evidence_refs=_list_of_str(raw.get("evidence_refs")),
                    metadata={
                        **_dict_or_empty(raw.get("metadata")),
                        "source": "counterfactual",
                        "created_from_counterfactual_metadata": True,
                    },
                )
            )

    def _build_run(
        self,
        request: CounterfactualRunRequest,
        frame: DecisionFrame,
        option: DecisionOption | None,
    ) -> CounterfactualRun:
        run_id = request.counterfactual_run_id or f"counterfactual-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="counterfactual_run_started",
            node_type="counterfactual",
            node_id=run_id,
            intensity=0.4,
            trace_id=request.trace_id or frame.trace_id,
            payload={"owner_scope": request.owner_scope, "mode": request.mode},
        )
        state_atoms = _state_atom_ids(self._state_atom_service, request.owner_scope)
        changes = list((option.expected_effects if option else [])[: request.max_projected_changes])
        unknowns = _unknowns(frame, option)
        risk_score = {"low": 0.05, "medium": 0.2, "high": 0.45, "critical": 0.7}.get(
            option.risk_level if option else "medium",
            0.2,
        )
        score = max(0.0, min(1.0, 1.0 - risk_score - (0.05 * len(unknowns))))
        now = datetime.now(UTC)
        run = CounterfactualRun(
            counterfactual_run_id=run_id,
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id if option else None,
            trace_id=request.trace_id or frame.trace_id,
            status="dry_run" if request.mode == "dry_run" else "completed",
            mode=request.mode,
            owner_scope=request.owner_scope,
            input_state=request.input_state,
            assumptions=request.assumptions,
            projected_changes=changes,
            projected_risks=[
                {
                    "risk_level": option.risk_level if option else "medium",
                    "source": "decision_option",
                }
            ],
            unknowns=unknowns,
            score=score,
            result={
                "mutated_source_records": False,
                "projected_from": "expected_effects_only",
                "state_atom_ids": state_atoms,
            },
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )
        if request.mode != "dry_run" or bool(
            getattr(self._settings, "decision_record_dry_run_counterfactuals", True)
        ):
            self._repository.save_counterfactual(run)
        emit_telemetry(
            self._telemetry_service,
            event_type="counterfactual_run_completed",
            node_type="counterfactual",
            node_id=run.counterfactual_run_id,
            intensity=run.score,
            trace_id=run.trace_id,
            payload={"owner_scope": run.owner_scope, "status": run.status},
        )
        if request.metadata.get("create_expected_effects") is True:
            self._create_expected_effects(run)
        return run

    def _blocked_run(
        self,
        request: CounterfactualRunRequest,
        frame: DecisionFrame,
        option: DecisionOption | None,
        status: str,
    ) -> CounterfactualRun:
        now = datetime.now(UTC)
        return CounterfactualRun(
            counterfactual_run_id=request.counterfactual_run_id or f"counterfactual-{uuid4().hex}",
            decision_frame_id=frame.decision_frame_id,
            decision_option_id=option.decision_option_id if option else request.decision_option_id,
            trace_id=request.trace_id or frame.trace_id,
            status=status,  # type: ignore[arg-type]
            mode=request.mode,
            owner_scope=request.owner_scope,
            input_state=request.input_state,
            assumptions=request.assumptions,
            projected_changes=[],
            projected_risks=[],
            unknowns=[status],
            score=0.0,
            result={"mutated_source_records": False, "blocked": status},
            created_by=request.created_by,
            created_at=now,
            completed_at=now,
        )


def _unknowns(frame: DecisionFrame, option: DecisionOption | None) -> list[str]:
    unknowns: list[str] = []
    if not frame.evidence_refs:
        unknowns.append("missing_evidence")
    if not frame.belief_refs:
        unknowns.append("missing_belief_support")
    if option is None or not option.action_type:
        unknowns.append("policy_unknown")
        unknowns.append("autonomy_unknown")
    if option and option.reversibility == "irreversible":
        unknowns.append("irreversible_effect")
    if option and option.risk_level in {"high", "critical"}:
        unknowns.append("approval_missing")
    return unknowns


def _state_atom_ids(service: object | None, scope: list[str]) -> list[str]:
    atoms = call_optional(service, ("list_atoms", "list"), scope=scope, limit=25)
    if not isinstance(atoms, list):
        return []
    return [
        str(getattr(item, "state_atom_id", ""))
        for item in atoms
        if getattr(item, "state_atom_id", None)
    ]


def _autonomy_allows(autonomy_governor: object | None) -> bool:
    if autonomy_governor is None:
        return True
    result = call_optional(
        autonomy_governor,
        ("authorize", "authorize_action", "decide"),
        action_type="decision.counterfactual.run",
        risk_level="medium",
    )
    return not (
        getattr(result, "allow", None) is False or getattr(result, "allowed", None) is False
    )


def _clamp(value: float) -> float:
    return max(0.0, min(1.0, value))


def _str_or_none(value: object) -> str | None:
    return value if isinstance(value, str) and value else None


def _dict_or_empty(value: object) -> dict[str, object]:
    return dict(value) if isinstance(value, dict) else {}


def _list_of_str(value: object) -> list[str]:
    if isinstance(value, list):
        return [str(item) for item in value]
    return []
