"""Deterministic grounded explanation builder."""

from __future__ import annotations

from typing import Any, cast
from uuid import uuid4

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.audit_integrity import ProvenanceLink
from aion_brain.contracts.explanations import (
    ExplanationRecord,
    ExplanationRequest,
    ExplanationStep,
)
from aion_brain.contracts.grounding import GroundingVerificationRequest
from aion_brain.explanations._shared import (
    authorize,
    clamp,
    emit_explanation_telemetry,
    items_from_source,
    now_utc,
    object_id,
    object_value,
    payload_scope,
    refs_from_object,
    safe_call,
    string_refs,
    unique,
)
from aion_brain.explanations.redaction import (
    redact_explanation_text,
    sanitize_explanation_payload,
)
from aion_brain.explanations.repository import ExplanationRepository
from aion_brain.explanations.templates import explanation_template
from aion_brain.explanations.verifier import ExplanationVerifier


class ExplanationBuilder:
    """Build public explanations from observable local AION records."""

    def __init__(
        self,
        explanation_repository: ExplanationRepository,
        policy_adapter: object,
        *,
        audit_ledger: object | None = None,
        provenance_service: object | None = None,
        policy_service: object | None = None,
        risk_service: object | None = None,
        approval_service: object | None = None,
        autonomy_service: object | None = None,
        evidence_service: object | None = None,
        memory_service: object | None = None,
        belief_service: object | None = None,
        decision_service: object | None = None,
        outcome_service: object | None = None,
        response_service: object | None = None,
        self_model_service: object | None = None,
        telemetry_service: object | None = None,
        settings: object | None = None,
        verifier: ExplanationVerifier | None = None,
        citation_mapper: object | None = None,
        grounding_verifier: object | None = None,
    ) -> None:
        self._repository = explanation_repository
        self._policy_adapter = policy_adapter
        self._audit_ledger = audit_ledger
        self._provenance_service = provenance_service
        self._policy_service = policy_service
        self._risk_service = risk_service
        self._approval_service = approval_service
        self._autonomy_service = autonomy_service
        self._evidence_service = evidence_service
        self._memory_service = memory_service
        self._belief_service = belief_service
        self._decision_service = decision_service
        self._outcome_service = outcome_service
        self._response_service = response_service
        self._self_model_service = self_model_service
        self._telemetry_service = telemetry_service
        self._settings = settings
        self._verifier = verifier or ExplanationVerifier(telemetry_service)
        self._citation_mapper = citation_mapper
        self._grounding_verifier = grounding_verifier

    def set_grounding_services(
        self,
        citation_mapper: object | None,
        grounding_verifier: object | None,
    ) -> None:
        """Attach grounding services after kernel assembly."""

        self._citation_mapper = citation_mapper
        self._grounding_verifier = grounding_verifier

    def explain(self, request: ExplanationRequest) -> ExplanationRecord:
        """Build, verify, optionally store, audit, and return an explanation."""

        if not bool(getattr(self._settings, "explanations_enabled", True)):
            raise RuntimeError("explanations_disabled")
        authorize(
            self._policy_adapter,
            action_type="explanation.create",
            resource_type=request.target_type,
            resource_id=request.target_id,
            scope=request.owner_scope,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            context={"explanation_type": request.explanation_type},
        )
        explanation_id = request.explanation_id or f"explanation-{uuid4().hex}"
        target = self._load_target(request)
        refs = self._collect_refs(request, target)
        summary, summary_redaction = redact_explanation_text(_summary_for(request, target, refs))
        metadata, metadata_redaction = sanitize_explanation_payload(
            {
                **request.metadata,
                "owner_scope": request.owner_scope,
                "require_grounding": request.require_grounding,
                "target_found": target is not None,
            }
        )
        steps = _steps_for(explanation_id, request, target, refs) if request.include_steps else []
        grounded = bool(refs["evidence_refs"] or refs["audit_refs"] or refs["provenance_refs"])
        status = _status_for(request, target, refs, grounded)
        confidence = _confidence_for(request, target, refs, grounded)
        explanation = ExplanationRecord(
            explanation_id=explanation_id,
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            explanation_type=request.explanation_type,
            target_type=request.target_type,
            target_id=request.target_id,
            status=cast(Any, status),
            title=_title_for(request),
            summary=summary,
            confidence=confidence,
            grounded=grounded,
            evidence_refs=refs["evidence_refs"] if request.include_evidence else [],
            memory_refs=refs["memory_refs"],
            belief_refs=refs["belief_refs"],
            decision_refs=refs["decision_refs"],
            outcome_refs=refs["outcome_refs"],
            audit_refs=refs["audit_refs"] if request.include_audit else [],
            provenance_refs=refs["provenance_refs"],
            policy_decision_id=refs["policy_decision_id"],
            autonomy_decision_id=refs["autonomy_decision_id"],
            risk_assessment_id=refs["risk_assessment_id"],
            approval_request_id=refs["approval_request_id"],
            steps=steps,
            redaction_metadata=_merge_redaction(summary_redaction, metadata_redaction),
            constraints=_constraints_for(request, refs, status),
            metadata=metadata,
            created_by=request.created_by,
            created_at=now_utc(),
        )
        verification = self._verifier.verify_explanation(explanation)
        if verification.status == "failed":
            explanation = explanation.model_copy(update={"status": "failed"})
        stored = (
            self._repository.save_explanation(explanation)
            if bool(getattr(self._settings, "explanation_store_records", True))
            else explanation
        )
        stored = self._apply_grounding_if_requested(request, stored)
        self._audit(request, stored, verification.status)
        self._provenance(request, stored)
        emit_explanation_telemetry(
            self._telemetry_service,
            event_type="explanation_created",
            node_type="explanation",
            node_id=stored.explanation_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            owner_scope=request.owner_scope,
            payload={
                "status": stored.status,
                "target_type": stored.target_type,
                "target_id": stored.target_id,
            },
        )
        return stored

    def _apply_grounding_if_requested(
        self,
        request: ExplanationRequest,
        explanation: ExplanationRecord,
    ) -> ExplanationRecord:
        if not request.include_evidence and not request.require_grounding:
            return explanation
        metadata = dict(explanation.metadata)
        try:
            map_text = getattr(self._citation_mapper, "map_text", None)
            if callable(map_text):
                citation_map = map_text(
                    text=explanation.summary,
                    trace_id=explanation.trace_id,
                    owner_scope=request.owner_scope,
                    sources=[],
                    target_type="explanation",
                    target_id=explanation.explanation_id,
                    required_source_types=["evidence"] if request.include_evidence else [],
                    metadata={"source": "explanation_builder"},
                )
                metadata["citation_map_id"] = citation_map.citation_map_id
            verify = getattr(self._grounding_verifier, "verify", None)
            if callable(verify) and request.require_grounding:
                run = verify(
                    GroundingVerificationRequest(
                        trace_id=explanation.trace_id,
                        explanation_id=explanation.explanation_id,
                        target_type="explanation",
                        target_id=explanation.explanation_id,
                        owner_scope=request.owner_scope,
                        text=explanation.summary,
                        required_source_types=["evidence"] if request.include_evidence else [],
                        require_evidence=request.include_evidence,
                        metadata={"source": "explanation_builder"},
                        created_by=request.created_by,
                    )
                )
                metadata["grounding_verification_id"] = run.grounding_verification_id
                metadata["grounding_status"] = run.status
        except Exception:
            metadata["grounding_status"] = "unavailable"
        updated = explanation.model_copy(update={"metadata": metadata})
        if bool(getattr(self._settings, "explanation_store_records", True)):
            return self._repository.save_explanation(updated)
        return updated

    def get(self, explanation_id: str, scope: list[str]) -> ExplanationRecord | None:
        """Return one explanation after policy authorization."""

        authorize(
            self._policy_adapter,
            action_type="explanation.read",
            resource_type="explanation",
            resource_id=explanation_id,
            scope=scope,
        )
        explanation = self._repository.get_explanation(explanation_id)
        if explanation is None:
            return None
        if not _scope_matches(explanation.metadata.get("owner_scope"), scope):
            return None
        return explanation

    def list(
        self,
        trace_id: str | None = None,
        target_type: str | None = None,
        target_id: str | None = None,
        limit: int = 50,
    ) -> list[ExplanationRecord]:
        """List explanations."""

        return self._repository.list_explanations(
            trace_id=trace_id,
            target_type=target_type,
            target_id=target_id,
            limit=limit,
        )

    def _load_target(self, request: ExplanationRequest) -> object | None:
        if request.target_id is None and request.trace_id is None:
            return None
        lookup_id = request.target_id or request.trace_id
        source = _source_for_target(self, request.target_type)
        return cast(
            object | None,
            safe_call(
                source,
                (
                    f"get_{request.target_type}",
                    "get",
                    "get_record",
                    "get_trace",
                    "get_response",
                    "get_request",
                    "get_decision",
                    "get_assessment",
                    "get_outcome",
                ),
                lookup_id,
                request.owner_scope,
            ),
        )

    def _collect_refs(
        self,
        request: ExplanationRequest,
        target: object | None,
    ) -> dict[str, Any]:
        metadata = request.metadata
        policy_decisions = _policy_decisions(self._policy_service, request)
        approvals = _approval_records(self._approval_service, request)
        audit_entries = _audit_entries(self._audit_ledger, request)
        provenance_links = _provenance_links(self._provenance_service, request)
        evidence_refs = unique(
            string_refs(metadata.get("evidence_refs"))
            + refs_from_object(target, "evidence_refs", "grounding_refs")
        )
        memory_refs = unique(
            string_refs(metadata.get("memory_refs")) + refs_from_object(target, "memory_refs")
        )
        belief_refs = unique(
            string_refs(metadata.get("belief_refs")) + refs_from_object(target, "belief_refs")
        )
        decision_refs = unique(
            string_refs(metadata.get("decision_refs"))
            + refs_from_object(target, "decision_refs")
            + [
                object_id(item, "decision_id", "decision_record_id") or ""
                for item in policy_decisions
            ]
        )
        outcome_refs = unique(
            string_refs(metadata.get("outcome_refs")) + refs_from_object(target, "outcome_refs")
        )
        audit_refs = unique(
            string_refs(metadata.get("audit_refs"))
            + [object_id(item, "audit_entry_id") or "" for item in audit_entries]
        )
        provenance_refs = unique(
            string_refs(metadata.get("provenance_refs"))
            + [object_id(item, "provenance_link_id") or "" for item in provenance_links]
        )
        approval_request_id = _first_ref(
            string_refs(metadata.get("approval_request_id"))
            + refs_from_object(target, "approval_request_id")
            + [object_id(item, "approval_request_id") or "" for item in approvals]
        )
        policy_decision_id = _first_ref(
            string_refs(metadata.get("policy_decision_id"))
            + refs_from_object(target, "policy_decision_id")
            + [object_id(item, "decision_id") or "" for item in policy_decisions]
        )
        return {
            "policy_decisions": policy_decisions,
            "approvals": approvals,
            "audit_entries": audit_entries,
            "provenance_links": provenance_links,
            "evidence_refs": evidence_refs,
            "memory_refs": memory_refs,
            "belief_refs": belief_refs,
            "decision_refs": decision_refs,
            "outcome_refs": outcome_refs,
            "audit_refs": audit_refs,
            "provenance_refs": provenance_refs,
            "policy_decision_id": policy_decision_id,
            "autonomy_decision_id": _first_ref(
                string_refs(metadata.get("autonomy_decision_id"))
                + refs_from_object(target, "autonomy_decision_id")
            ),
            "risk_assessment_id": _first_ref(
                string_refs(metadata.get("risk_assessment_id"))
                + refs_from_object(target, "risk_assessment_id")
            ),
            "approval_request_id": approval_request_id,
            "policy_blocked": any(
                not bool(object_value(item, "allow", True)) for item in policy_decisions
            )
            or bool(metadata.get("policy_blocked")),
            "approval_required": bool(approval_request_id)
            or any(str(object_value(item, "status", "")) == "pending" for item in approvals)
            or bool(metadata.get("approval_required")),
            "autonomy_blocked": bool(metadata.get("autonomy_blocked")),
            "capability_unavailable": bool(metadata.get("capability_unavailable")),
        }

    def _audit(
        self,
        request: ExplanationRequest,
        explanation: ExplanationRecord,
        verification_status: str,
    ) -> None:
        record_audit_event(
            self._audit_ledger,
            action_type="explanation.create",
            resource_type="explanation",
            resource_id=explanation.explanation_id,
            event_type="explanation_created",
            outcome="completed" if explanation.status != "failed" else "failed",
            source_component="explanation_builder",
            trace_id=explanation.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            policy_decision_id=explanation.policy_decision_id,
            autonomy_decision_id=explanation.autonomy_decision_id,
            risk_assessment_id=explanation.risk_assessment_id,
            approval_request_id=explanation.approval_request_id,
            payload={
                "target_type": explanation.target_type,
                "target_id": explanation.target_id,
                "verification_status": verification_status,
                "grounded": explanation.grounded,
            },
            metadata={"owner_scope": request.owner_scope},
        )

    def _provenance(self, request: ExplanationRequest, explanation: ExplanationRecord) -> None:
        create_link = getattr(self._provenance_service, "create_link", None)
        if not callable(create_link) or not explanation.target_id:
            return
        target_type = _provenance_type(explanation.target_type)
        if target_type is None:
            return
        try:
            create_link(
                ProvenanceLink(
                    provenance_link_id=f"provenance-{uuid4().hex}",
                    trace_id=explanation.trace_id,
                    source_type="explanation",
                    source_id=explanation.explanation_id,
                    target_type=target_type,
                    target_id=explanation.target_id,
                    relation_type="referenced",
                    confidence=explanation.confidence,
                    audit_entry_id=None,
                    evidence_refs=explanation.evidence_refs,
                    metadata={"source": "explanation_builder", "owner_scope": request.owner_scope},
                )
            )
        except Exception:
            return


def _source_for_target(builder: ExplanationBuilder, target_type: str) -> object | None:
    mapping = {
        "response": builder._response_service,
        "policy": builder._policy_service,
        "risk": builder._risk_service,
        "approval": builder._approval_service,
        "autonomy": builder._autonomy_service,
        "evidence": builder._evidence_service,
        "memory": builder._memory_service,
        "belief": builder._belief_service,
        "decision": builder._decision_service,
        "outcome": builder._outcome_service,
        "capability": builder._self_model_service,
        "trace": builder._policy_service,
    }
    return mapping.get(target_type)


def _policy_decisions(source: object | None, request: ExplanationRequest) -> list[Any]:
    if not request.include_policy:
        return []
    if request.trace_id:
        return items_from_source(
            source, ("list_policy_decisions", "list_decisions"), request.trace_id
        )
    decision_id = request.metadata.get("policy_decision_id")
    if decision_id:
        return items_from_source(
            source, ("get_policy_decision", "get_decision", "get"), decision_id
        )
    return []


def _approval_records(source: object | None, request: ExplanationRequest) -> list[Any]:
    approval_id = request.metadata.get("approval_request_id")
    if approval_id:
        return items_from_source(
            source, ("get_request", "get", "get_approval"), approval_id, request.owner_scope
        )
    return items_from_source(source, ("list_pending", "list_requests", "list"), request.owner_scope)


def _audit_entries(source: object | None, request: ExplanationRequest) -> list[Any]:
    if not request.include_audit:
        return []
    return items_from_source(
        source,
        ("list_entries", "list"),
        trace_id=request.trace_id,
        limit=50,
        ascending=True,
    )


def _provenance_links(source: object | None, request: ExplanationRequest) -> list[Any]:
    if not request.include_audit:
        return []
    return items_from_source(
        source, ("graph_for_trace", "list_links"), trace_id=request.trace_id, limit=50
    )


def _summary_for(
    request: ExplanationRequest,
    target: object | None,
    refs: dict[str, Any],
) -> str:
    if refs["policy_blocked"]:
        return explanation_template("policy_blocked")
    if refs["autonomy_blocked"]:
        return explanation_template("autonomy_blocked")
    if refs["approval_required"]:
        return explanation_template("approval_required")
    if refs["capability_unavailable"]:
        return explanation_template("capability_unavailable")
    if request.require_grounding and not refs["evidence_refs"]:
        return explanation_template("low_confidence")
    if target is None:
        return "AION found limited observable records for this target."
    if request.explanation_type == "retrieval":
        return explanation_template("retrieval_choice")
    if request.explanation_type == "decision":
        return explanation_template("decision_recommendation")
    if request.explanation_type == "outcome":
        return explanation_template("outcome_partial")
    return explanation_template(request.explanation_type)


def _title_for(request: ExplanationRequest) -> str:
    target = request.target_id or request.trace_id or request.target_type
    return f"Explanation for {request.target_type} {target}".strip()


def _steps_for(
    explanation_id: str,
    request: ExplanationRequest,
    target: object | None,
    refs: dict[str, Any],
) -> list[ExplanationStep]:
    steps: list[ExplanationStep] = []
    step_order = 1
    steps.append(
        _step(
            explanation_id,
            step_order,
            "generic",
            "Target inspected",
            "AION inspected observable local records for the requested target.",
            request.target_type,
            request.target_id,
            [request.target_id] if request.target_id else [],
            0.7 if target is not None else 0.3,
        )
    )
    step_order += 1
    if refs["policy_decisions"]:
        steps.append(
            _step(
                explanation_id,
                step_order,
                "policy",
                "Policy records checked",
                "Policy decisions were included where available.",
                "policy",
                refs["policy_decision_id"],
                refs["decision_refs"],
                0.8,
            )
        )
        step_order += 1
    if refs["approval_required"]:
        steps.append(
            _step(
                explanation_id,
                step_order,
                "approval",
                "Approval requirement found",
                "An approval record or approval requirement is linked to this explanation.",
                "approval",
                refs["approval_request_id"],
                [refs["approval_request_id"]] if refs["approval_request_id"] else [],
                0.8,
            )
        )
        step_order += 1
    if refs["evidence_refs"]:
        steps.append(
            _step(
                explanation_id,
                step_order,
                "evidence",
                "Evidence references collected",
                "Evidence references were available for grounding.",
                "evidence",
                None,
                refs["evidence_refs"],
                0.8,
            )
        )
    return steps


def _step(
    explanation_id: str,
    step_order: int,
    step_type: str,
    title: str,
    description: str,
    source_type: str | None,
    source_id: str | None,
    refs: list[str],
    confidence: float,
) -> ExplanationStep:
    return ExplanationStep(
        explanation_step_id=f"explanation-step-{uuid4().hex}",
        explanation_id=explanation_id,
        step_order=step_order,
        step_type=cast(Any, step_type),
        title=title,
        description=description,
        source_type=source_type,
        source_id=source_id,
        refs=unique(refs),
        confidence=confidence,
        metadata={},
        created_at=now_utc(),
    )


def _status_for(
    request: ExplanationRequest,
    target: object | None,
    refs: dict[str, Any],
    grounded: bool,
) -> str:
    if refs["policy_blocked"]:
        return "blocked_by_policy"
    if request.require_grounding and not refs["evidence_refs"]:
        return "insufficient_evidence"
    if target is None and not grounded:
        return "partial"
    return "completed"


def _confidence_for(
    request: ExplanationRequest,
    target: object | None,
    refs: dict[str, Any],
    grounded: bool,
) -> float:
    confidence = 0.5
    confidence += 0.1 if refs["evidence_refs"] else 0.0
    confidence += 0.1 if refs["audit_refs"] else 0.0
    confidence += 0.1 if refs["provenance_refs"] else 0.0
    confidence -= 0.2 if target is None else 0.0
    confidence -= 0.25 if request.require_grounding and not refs["evidence_refs"] else 0.0
    confidence += 0.05 if grounded else 0.0
    return clamp(confidence)


def _constraints_for(
    request: ExplanationRequest,
    refs: dict[str, Any],
    status: str,
) -> list[str]:
    constraints: list[str] = []
    if status == "insufficient_evidence":
        constraints.append("insufficient_evidence")
    if refs["policy_blocked"]:
        constraints.append("policy_blocked")
    if refs["approval_required"]:
        constraints.append("approval_required")
    if request.metadata.get("constraints"):
        constraints.extend(string_refs(request.metadata["constraints"]))
    return unique(constraints)


def _first_ref(values: list[str]) -> str | None:
    return next((value for value in values if value), None)


def _merge_redaction(*items: dict[str, Any]) -> dict[str, Any]:
    return {
        "redacted": any(bool(item.get("redacted")) for item in items),
        "redaction_count": sum(int(item.get("redaction_count", 0)) for item in items),
        "removed_count": sum(int(item.get("removed_count", 0)) for item in items),
        "field_paths": [path for item in items for path in item.get("field_paths", [])],
        "removed_field_paths": [
            path for item in items for path in item.get("removed_field_paths", [])
        ],
    }


def _scope_matches(value: Any, scope: list[str]) -> bool:
    owner_scope = payload_scope({"owner_scope": value}, [])
    return not owner_scope or bool(set(owner_scope) & set(scope))


def _provenance_type(target_type: str) -> Any | None:
    allowed = {
        "event",
        "command",
        "memory",
        "evidence",
        "trace",
        "reasoning",
        "plan",
        "execution",
        "workflow",
        "task",
        "goal",
        "approval",
        "policy",
        "risk",
        "autonomy",
        "capability",
        "module",
        "mcp",
        "sandbox",
        "response",
        "explanation",
        "trace_narrative",
        "why_not",
    }
    return target_type if target_type in allowed else None


__all__ = ["ExplanationBuilder"]
