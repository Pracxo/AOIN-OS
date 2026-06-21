"""Operator Action Center service."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.operator import (
    OperatorAcknowledgement,
    OperatorAcknowledgementRequest,
    OperatorActionItem,
    OperatorSeverity,
)
from aion_brain.contracts.policy import PolicyRequest
from aion_brain.contracts.telemetry import VisualTelemetryEvent
from aion_brain.operator.repository import OperatorRepository

_FAILED_STATUSES = {"failed", "error", "critical"}
_OPEN_CIRCUIT_STATUSES = {"open", "half_open"}
_PENDING_APPROVAL_STATUSES = {"pending"}


class ActionCenterService:
    """Build generic local operator action items without executing actions."""

    def __init__(
        self,
        repository: OperatorRepository,
        policy_adapter: object | None = None,
        telemetry_service: object | None = None,
        **sources: object,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._sources = sources

    def build_action_items(self, scope: list[str], limit: int = 100) -> list[OperatorActionItem]:
        """Build and persist action recommendations from read-only local state."""
        self._authorize("operator.actions.read", scope, "operator_action_items", None)
        generated: list[OperatorActionItem] = []
        generated.extend(self._pending_approval_items(scope))
        generated.extend(self._failed_command_items())
        generated.extend(self._open_circuit_breaker_items())
        generated.extend(self._failed_audit_verification_items())
        generated.extend(self._belief_contradiction_items(scope))
        generated.extend(self._unresolved_entity_mention_items(scope))
        generated.extend(self._entity_merge_items(scope))
        generated.extend(self._entity_split_items(scope))
        generated.extend(self._stale_situation_items(scope))
        generated.extend(self._failed_projection_items())
        generated.extend(self._open_decision_frame_items(scope))
        generated.extend(self._high_risk_decision_items(scope))
        generated.extend(self._failed_counterfactual_items())
        generated.extend(self._failed_outcome_items(scope))
        generated.extend(self._failed_effect_verification_items())
        generated.extend(self._failed_grounding_items(scope))
        generated.extend(self._low_source_coverage_items(scope))
        generated.extend(self._prompt_injection_items(scope))
        generated.extend(self._high_severity_outcome_feedback_items())
        generated.extend(self._high_severity_learning_pattern_items(scope))
        generated.extend(self._open_skill_suggestion_items(scope))
        generated.extend(self._open_regression_suggestion_items(scope))
        generated.extend(self._failed_learning_synthesis_items(scope))
        generated.extend(self._critical_limitation_items(scope))
        generated.extend(self._failed_explanation_items(scope))
        generated.extend(self._instruction_conflict_items(scope))
        generated.extend(self._preference_candidate_items(scope))
        stored: list[OperatorActionItem] = []
        for item in generated[:limit]:
            saved = self._repository.save_action_item(item)
            stored.append(saved)
            if saved.action_item_id == item.action_item_id and saved.created_at == item.created_at:
                self._emit_action_created(saved)
        existing = self._repository.list_action_items(status="open", limit=limit)
        by_id = {item.action_item_id: item for item in [*stored, *existing]}
        return list(by_id.values())[:limit]

    def acknowledge(
        self,
        request: OperatorAcknowledgementRequest,
    ) -> OperatorAcknowledgement:
        """Record acknowledgement without resolving or mutating the source issue."""
        self._authorize(
            "operator.acknowledgement.create",
            ["workspace:main"],
            request.source_type,
            request.source_id,
        )
        acknowledgement = OperatorAcknowledgement(
            acknowledgement_id=request.acknowledgement_id or f"ack-{uuid4().hex}",
            action_item_id=request.action_item_id,
            source_type=request.source_type,
            source_id=request.source_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            reason=request.reason,
            metadata=request.metadata,
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_acknowledgement(acknowledgement)
        if request.action_item_id:
            self._repository.acknowledge_action_item(request.action_item_id)
        self._emit_acknowledged(stored)
        return stored

    def list_acknowledgements(
        self,
        source_type: str | None = None,
        source_id: str | None = None,
        limit: int = 100,
    ) -> list[OperatorAcknowledgement]:
        """List local acknowledgement records."""
        self._authorize(
            "operator.acknowledgement.read",
            ["workspace:main"],
            source_type or "operator_acknowledgement",
            source_id,
        )
        return self._repository.list_acknowledgements(
            source_type=source_type,
            source_id=source_id,
            limit=limit,
        )

    def _pending_approval_items(self, scope: list[str]) -> list[OperatorActionItem]:
        items = _list_from(
            self._sources.get("approval_service"),
            ("list_requests", "list"),
            scope,
        )
        return [
            _action_item(
                source_type="approval",
                source_id=_id_for(item, "approval_request_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity=_approval_severity(item),
                title="Pending approval requires review.",
                description="A local approval request is waiting for operator review.",
                recommended_action="review_pending_approval",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, scope, "approval_scope"),
                metadata={"status": getattr(item, "status", "pending")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _PENDING_APPROVAL_STATUSES
        ]

    def _critical_limitation_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("limitation_service")
        list_limitations = getattr(source, "list_limitations", None)
        if not callable(list_limitations):
            return []
        try:
            items = list_limitations(scope, status="active", severity="critical")
        except Exception:
            return []
        return [
            _action_item(
                source_type="limitation",
                source_id=_id_for(item, "limitation_id"),
                trace_id=None,
                category="self_model",
                severity="critical",
                title="Critical limitation requires review.",
                description="A disclosed AION self-model limitation is marked critical.",
                recommended_action="review_limitation_disclosure",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "limitation_key": getattr(item, "limitation_key", None),
                    "status": getattr(item, "status", "active"),
                },
            )
            for item in items
        ]

    def _failed_explanation_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("explanation_service") or self._sources.get(
            "explanation_builder"
        )
        list_explanations = getattr(source, "list", None)
        if not callable(list_explanations):
            return []
        try:
            items = list_explanations(limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "explanation_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity="medium",
                title="Explanation verification requires inspection.",
                description="An explanation record is failed or insufficiently grounded.",
                recommended_action="review_explanation_record",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "explanation_id": getattr(item, "explanation_id", None),
                    "status": getattr(item, "status", "failed"),
                },
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in {"failed", "insufficient_evidence"}
        ]

    def _failed_command_items(self) -> list[OperatorActionItem]:
        items = _list_from(self._sources.get("command_service"), ("list_commands", "list"), [])
        return [
            _action_item(
                source_type="command",
                source_id=_id_for(item, "command_id"),
                trace_id=getattr(item, "trace_id", None),
                category="commands",
                severity="high",
                title="Failed command requires inspection.",
                description="A local command ended in a failed state.",
                recommended_action="inspect_failed_command",
                runbook_ref="docs/operations/local-ops-runbook.md",
                scope=["workspace:main"],
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _FAILED_STATUSES
        ]

    def _failed_grounding_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("grounding_verifier")
        list_runs = getattr(source, "list_verification_runs", None)
        if not callable(list_runs):
            return []
        try:
            items = list_runs(limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "grounding_verification_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity="high",
                title="Grounding verification requires review.",
                description="A deterministic grounding verification failed or lacks sources.",
                recommended_action="review_grounding_verification",
                runbook_ref="docs/grounding-model.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "failed"),
                    "coverage_score": getattr(item, "coverage_score", 0.0),
                },
            )
            for item in items
            if str(getattr(item, "status", "")).lower()
            in {"failed", "insufficient_sources", "blocked_by_policy"}
        ]

    def _low_source_coverage_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("source_coverage_service")
        repository = getattr(source, "_repository", None)
        list_reports = getattr(repository, "list_coverage_reports", None)
        if not callable(list_reports):
            return []
        try:
            items = list_reports(limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "source_coverage_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity="medium",
                title="Low source coverage requires review.",
                description="A response or explanation has weak source coverage.",
                recommended_action="improve_source_coverage",
                runbook_ref="docs/grounding-model.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "warning"),
                    "coverage_score": getattr(item, "coverage_score", 0.0),
                },
            )
            for item in items
            if float(getattr(item, "coverage_score", 1.0)) < 0.65
        ]

    def _instruction_conflict_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("instruction_conflict_service")
        list_conflicts = getattr(source, "list_conflicts", None)
        if not callable(list_conflicts):
            return []
        try:
            items = list_conflicts(scope, status="open", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "conflict_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity=cast(OperatorSeverity, getattr(item, "severity", "medium")),
                title="Instruction conflict requires review.",
                description="A high-severity instruction conflict is open.",
                recommended_action="review_instruction_conflict",
                runbook_ref="docs/instruction-hierarchy.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "conflict_type": getattr(item, "conflict_type", None),
                    "status": getattr(item, "status", "open"),
                },
            )
            for item in items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ]

    def _prompt_injection_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("prompt_repository")
        list_findings = getattr(source, "list_injection_findings", None)
        if not callable(list_findings):
            return []
        try:
            items = list_findings(status="open", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "injection_finding_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity=cast(OperatorSeverity, getattr(item, "severity", "medium")),
                title="Prompt injection finding requires review.",
                description="A high-severity prompt boundary finding is open.",
                recommended_action="review_prompt_injection_finding",
                runbook_ref="docs/prompt-governance.md",
                scope=scope or ["workspace:main"],
                metadata={
                    "finding_type": getattr(item, "finding_type", None),
                    "prompt_packet_id": getattr(item, "prompt_packet_id", None),
                },
            )
            for item in items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ]

    def _preference_candidate_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("preference_learning_service")
        list_candidates = getattr(source, "list_candidates", None)
        if not callable(list_candidates):
            return []
        try:
            items = list_candidates(scope, status="proposed", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "candidate_id"),
                trace_id=getattr(item, "trace_id", None),
                category="operator",
                severity="medium",
                title="Preference candidate requires confirmation.",
                description="A learned preference candidate is awaiting explicit review.",
                recommended_action="review_preference_candidate",
                runbook_ref="docs/instruction-hierarchy.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "preference_key": getattr(item, "preference_key", None),
                    "status": getattr(item, "status", "proposed"),
                },
            )
            for item in items
        ]

    def _failed_outcome_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("outcome_service")
        list_outcomes = getattr(source, "list_outcomes", None)
        if not callable(list_outcomes):
            return []
        try:
            items = list_outcomes(scope=scope, limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="outcome",
                source_id=_id_for(item, "outcome_id"),
                trace_id=getattr(item, "trace_id", None),
                category="audit",
                severity="high",
                title="Failed outcome requires inspection.",
                description="An outcome record reports failed or contradicted effects.",
                recommended_action="review_outcome_verification",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "failed"),
                    "score": getattr(item, "score", None),
                },
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in {"failed", "contradicted"}
        ]

    def _failed_effect_verification_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("effect_verifier")
        list_runs = getattr(source, "list_verification_runs", None)
        if not callable(list_runs):
            return []
        try:
            items = list_runs(status="failed", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="effect_verification",
                source_id=_id_for(item, "verification_run_id"),
                trace_id=getattr(item, "trace_id", None),
                category="audit",
                severity="high",
                title="Effect verification failed.",
                description=(
                    "A deterministic effect verification found missing or contradicted effects."
                ),
                recommended_action="review_effect_verification",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=_scope_for(item, ["workspace:main"], "owner_scope"),
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in items
        ]

    def _high_severity_outcome_feedback_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("outcome_feedback_service")
        list_feedback = getattr(source, "list_feedback", None)
        if not callable(list_feedback):
            return []
        try:
            items = list_feedback(status="open", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="outcome_feedback",
                source_id=_id_for(item, "outcome_feedback_id"),
                trace_id=getattr(item, "trace_id", None),
                category="audit",
                severity=cast(OperatorSeverity, str(getattr(item, "severity", "high"))),
                title="Outcome feedback requires review.",
                description="High-severity outcome feedback is open.",
                recommended_action="review_outcome_feedback",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=["workspace:main"],
                metadata={
                    "status": getattr(item, "status", "open"),
                    "feedback_type": getattr(item, "feedback_type", None),
                },
            )
            for item in items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ]

    def _high_severity_learning_pattern_items(
        self,
        scope: list[str],
    ) -> list[OperatorActionItem]:
        source = self._sources.get("learning_synthesis_repository")
        list_patterns = getattr(source, "list_patterns", None)
        if not callable(list_patterns):
            return []
        try:
            items = list_patterns(scope, status="active", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="learning_pattern",
                source_id=_id_for(item, "pattern_id"),
                trace_id=getattr(item, "trace_id", None),
                category="learning",
                severity=cast(OperatorSeverity, str(getattr(item, "severity", "high"))),
                title="Learning pattern requires review.",
                description="A high-severity learning pattern is waiting for review.",
                recommended_action="review_learning_pattern",
                runbook_ref="docs/learning-loop.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "active"),
                    "pattern_type": getattr(item, "pattern_type", None),
                },
            )
            for item in items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ]

    def _open_skill_suggestion_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("skill_suggestion_service")
        list_suggestions = getattr(source, "list_suggestions", None)
        if not callable(list_suggestions):
            return []
        try:
            items = list_suggestions(scope, status="suggested", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="skill_suggestion",
                source_id=_id_for(item, "suggestion_id"),
                trace_id=getattr(item, "trace_id", None),
                category="learning",
                severity=cast(OperatorSeverity, str(getattr(item, "risk_level", "medium"))),
                title="Skill suggestion requires review.",
                description="A passive skill candidate suggestion is open.",
                recommended_action="review_skill_candidate_suggestion",
                runbook_ref="docs/learning-loop.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "suggested"),
                    "promotion_allowed": getattr(item, "promotion_allowed", False),
                },
            )
            for item in items
        ]

    def _open_regression_suggestion_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("regression_suggestion_service")
        list_suggestions = getattr(source, "list_suggestions", None)
        if not callable(list_suggestions):
            return []
        try:
            items = list_suggestions(scope, status="suggested", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="regression_suggestion",
                source_id=_id_for(item, "regression_suggestion_id"),
                trace_id=getattr(item, "trace_id", None),
                category="learning",
                severity=cast(OperatorSeverity, str(getattr(item, "severity", "medium"))),
                title="Regression suggestion requires review.",
                description="A passive regression candidate suggestion is open.",
                recommended_action="review_regression_candidate_suggestion",
                runbook_ref="docs/learning-loop.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={
                    "status": getattr(item, "status", "suggested"),
                    "regression_case_created": False,
                },
            )
            for item in items
        ]

    def _failed_learning_synthesis_items(
        self,
        scope: list[str],
    ) -> list[OperatorActionItem]:
        source = self._sources.get("learning_synthesis_repository")
        list_runs = getattr(source, "list_synthesis_runs", None)
        if not callable(list_runs):
            return []
        try:
            items = list_runs(scope, status="failed", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="learning_synthesis",
                source_id=_id_for(item, "synthesis_run_id"),
                trace_id=getattr(item, "trace_id", None),
                category="learning",
                severity="high",
                title="Learning synthesis failed.",
                description="A deterministic learning synthesis run failed.",
                recommended_action="inspect_learning_synthesis_run",
                runbook_ref="docs/learning-loop.md",
                scope=_scope_for(item, scope, "owner_scope"),
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in items
        ]

    def _open_circuit_breaker_items(self) -> list[OperatorActionItem]:
        items = _list_from(
            self._sources.get("resilience_service"),
            ("list_circuit_breakers", "list"),
            [],
        )
        return [
            _action_item(
                source_type="resilience",
                source_id=_id_for(item, "name"),
                trace_id=None,
                category="resilience",
                severity="critical",
                title="Open circuit breaker requires inspection.",
                description="A local circuit breaker is open or half-open.",
                recommended_action="inspect_degraded_component",
                runbook_ref="docs/operations/resilience.md",
                scope=["workspace:main"],
                metadata={"status": getattr(item, "status", "open")},
            )
            for item in items
            if str(getattr(item, "status", "")).lower() in _OPEN_CIRCUIT_STATUSES
        ]

    def _failed_audit_verification_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("audit_service")
        latest = _call_optional(source, ("latest_verification_run", "latest_verification"))
        if latest is None:
            return []
        if str(getattr(latest, "status", "")).lower() not in _FAILED_STATUSES:
            return []
        return [
            _action_item(
                source_type="audit",
                source_id=_id_for(latest, "audit_verification_id"),
                trace_id=getattr(latest, "trace_id", None),
                category="audit",
                severity="critical",
                title="Audit verification failed.",
                description="A local audit integrity verification reported a failure.",
                recommended_action="run_audit_verification",
                runbook_ref="docs/operations/audit-integrity.md",
                scope=["workspace:main"],
                metadata={"status": getattr(latest, "status", "failed")},
            )
        ]

    def _belief_contradiction_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("belief_contradiction_service")
        list_contradictions = getattr(source, "list_contradictions", None)
        if not callable(list_contradictions):
            return []
        try:
            items = list_contradictions(scope, status="open", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "contradiction_id"),
                trace_id=getattr(item, "trace_id", None),
                category="memory",
                severity=cast(OperatorSeverity, str(getattr(item, "severity", "high"))),
                title="Belief contradiction requires review.",
                description="A high-severity belief contradiction is open.",
                recommended_action="review_belief_contradiction",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={
                    "status": getattr(item, "status", "open"),
                    "claim_id": getattr(item, "claim_id", None),
                },
            )
            for item in items
            if str(getattr(item, "severity", "")).lower() in {"high", "critical"}
        ]

    def _unresolved_entity_mention_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("entity_repository")
        list_mentions = getattr(source, "list_mentions", None)
        if not callable(list_mentions):
            return []
        try:
            mentions = list_mentions(
                scope=scope,
                resolved=False,
                min_confidence=0.7,
                limit=100,
            )
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "mention_id"),
                trace_id=getattr(item, "trace_id", None),
                category="memory",
                severity="medium",
                title="Unresolved entity mention requires review.",
                description=(
                    "A high-confidence mention could not be resolved to a canonical entity."
                ),
                recommended_action="review_entity_mention",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={
                    "status": "unresolved",
                    "source_type": getattr(item, "source_type", None),
                    "source_id": getattr(item, "source_id", None),
                },
            )
            for item in mentions
        ]

    def _entity_merge_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("entity_merge_service")
        list_proposals = getattr(source, "list_proposals", None)
        if not callable(list_proposals):
            return []
        try:
            proposals = list_proposals(scope, status="proposed")
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "merge_proposal_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity="medium",
                title="Entity merge proposal requires review.",
                description="A canonical entity merge has been proposed and needs approval.",
                recommended_action="review_entity_merge_proposal",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={"status": getattr(item, "status", "proposed")},
            )
            for item in proposals
        ]

    def _entity_split_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("entity_split_service")
        list_proposals = getattr(source, "list_proposals", None)
        if not callable(list_proposals):
            return []
        try:
            proposals = list_proposals(scope, status="proposed")
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "split_proposal_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity="medium",
                title="Entity split proposal requires review.",
                description="A canonical entity split has been proposed and needs approval.",
                recommended_action="review_entity_split_proposal",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={"status": getattr(item, "status", "proposed")},
            )
            for item in proposals
        ]

    def _stale_situation_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("situation_service")
        query = getattr(source, "query", None)
        if not callable(query):
            return []
        try:
            from aion_brain.contracts.situations import SituationQuery

            result = query(SituationQuery(scope=scope, statuses=["stale"], limit=100))
            situations = result.situations
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "situation_id"),
                trace_id=getattr(item, "trace_id", None),
                category="memory",
                severity="medium",
                title="Stale active situation requires review.",
                description=(
                    "A local situation projection is stale and may need refresh or closure."
                ),
                recommended_action="review_stale_situation",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={"status": getattr(item, "status", "stale")},
            )
            for item in situations
        ]

    def _failed_projection_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("situation_projector")
        list_failed_runs = getattr(source, "list_failed_runs", None)
        if not callable(list_failed_runs):
            return []
        try:
            runs = list_failed_runs(limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "projection_run_id"),
                trace_id=getattr(item, "trace_id", None),
                category="memory",
                severity="medium",
                title="Situation projection failed.",
                description="A local situation projection run ended in a failed state.",
                recommended_action="inspect_situation_projection",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=getattr(item, "owner_scope", ["workspace:main"]),
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in runs
        ]

    def _open_decision_frame_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("decision_frame_service")
        list_frames = getattr(source, "list_frames", None)
        if not callable(list_frames):
            return []
        try:
            frames = list_frames(scope, status="open", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "decision_frame_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity="medium",
                title="Open decision frame requires review.",
                description="A local decision frame is open and may need evaluation or closure.",
                recommended_action="review_open_decision_frame",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={"status": getattr(item, "status", "open")},
            )
            for item in frames
        ]

    def _high_risk_decision_items(self, scope: list[str]) -> list[OperatorActionItem]:
        source = self._sources.get("decision_journal_service")
        list_records = getattr(source, "list_records", None)
        if not callable(list_records):
            return []
        try:
            records = list_records(scope, status="recorded", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "decision_record_id"),
                trace_id=getattr(item, "trace_id", None),
                category="approvals",
                severity="high",
                title="Decision recommendation is waiting for approval.",
                description="A high-risk selected option was recorded without approval.",
                recommended_action="review_decision_approval_requirement",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=scope,
                metadata={"approval_request_id": getattr(item, "approval_request_id", None)},
            )
            for item in records
            if getattr(item, "approval_request_id", None)
        ]

    def _failed_counterfactual_items(self) -> list[OperatorActionItem]:
        source = self._sources.get("counterfactual_simulator")
        repository = getattr(source, "_repository", None)
        list_runs = getattr(repository, "list_counterfactual_runs", None)
        if not callable(list_runs):
            return []
        try:
            runs = list_runs(status="failed", limit=100)
        except Exception:
            return []
        return [
            _action_item(
                source_type="generic",
                source_id=_id_for(item, "counterfactual_run_id"),
                trace_id=getattr(item, "trace_id", None),
                category="memory",
                severity="medium",
                title="Counterfactual run failed.",
                description="A local counterfactual simulation ended in a failed state.",
                recommended_action="inspect_counterfactual_run",
                runbook_ref="docs/operations/operator-control-tower.md",
                scope=getattr(item, "owner_scope", ["workspace:main"]),
                metadata={"status": getattr(item, "status", "failed")},
            )
            for item in runs
        ]

    def _authorize(
        self,
        action_type: str,
        scope: list[str],
        resource_type: str,
        resource_id: str | None,
    ) -> None:
        authorize = getattr(self._policy_adapter, "authorize", None)
        if not callable(authorize):
            return
        decision = authorize(
            PolicyRequest(
                request_id=f"operator-{uuid4().hex}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type=action_type,
                resource_type=resource_type,
                resource_id=resource_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[action_type],
                security_scope=scope,
                context={"source": "operator_action_center"},
            )
        )
        if not decision.allow:
            raise PermissionError(decision.reason)

    def _emit_action_created(self, item: OperatorActionItem) -> None:
        _emit(
            self._telemetry_service,
            "operator_action_item_created",
            "action_item",
            item.action_item_id,
            _intensity_for(item.severity),
            {"severity": item.severity, "source_type": item.source_type},
            item.trace_id,
        )

    def _emit_acknowledged(self, acknowledgement: OperatorAcknowledgement) -> None:
        _emit(
            self._telemetry_service,
            "operator_action_acknowledged",
            "action_item",
            acknowledgement.action_item_id or acknowledgement.source_id,
            0.3,
            {"source_type": acknowledgement.source_type},
            None,
        )


def _action_item(
    *,
    source_type: str,
    source_id: str,
    trace_id: str | None,
    category: str,
    severity: OperatorSeverity,
    title: str,
    description: str,
    recommended_action: str,
    runbook_ref: str,
    scope: list[str],
    metadata: dict[str, Any],
) -> OperatorActionItem:
    return OperatorActionItem(
        action_item_id=f"action-{source_type}-{source_id}",
        trace_id=trace_id,
        source_type=cast(Any, source_type),
        source_id=source_id,
        category=cast(Any, category),
        severity=severity,
        status="open",
        title=title,
        description=description,
        recommended_action=recommended_action,
        runbook_ref=runbook_ref,
        owner_scope=scope or ["workspace:main"],
        metadata=metadata,
        created_at=datetime.now(UTC),
    )


def _list_from(source: object | None, methods: tuple[str, ...], scope: list[str]) -> list[object]:
    if source is None:
        return []
    for name in methods:
        method = getattr(source, name, None)
        if callable(method):
            callable_method = cast(Any, method)
            if name == "list_requests":
                try:
                    from aion_brain.contracts.approvals import ApprovalInboxQuery

                    return list(
                        callable_method(
                            ApprovalInboxQuery(scope=scope or ["workspace:main"], limit=100)
                        )
                        or []
                    )
                except (ImportError, TypeError):
                    pass
            attempts: tuple[dict[str, object], ...] = (
                {"scope": scope, "limit": 100},
                {"scope": scope},
                {"status": None, "limit": 100},
                {"limit": 100},
                {},
            )
            for kwargs in attempts:
                try:
                    return list(callable_method(**kwargs) or [])
                except TypeError:
                    continue
    return []


def _call_optional(source: object | None, methods: tuple[str, ...]) -> object | None:
    if source is None:
        return None
    for name in methods:
        method = getattr(source, name, None)
        if callable(method):
            callable_method = cast(Any, method)
            return cast(object, callable_method())
    return None


def _id_for(item: object, attr: str) -> str:
    value = getattr(item, attr, None)
    if value is not None:
        return str(value)
    return uuid4().hex


def _scope_for(item: object, fallback: list[str], attr: str) -> list[str]:
    value = getattr(item, attr, None)
    if isinstance(value, list) and value:
        return [str(entry) for entry in value]
    return fallback or ["workspace:main"]


def _approval_severity(item: object) -> OperatorSeverity:
    priority = str(getattr(item, "priority", "")).lower()
    if priority in {"urgent"}:
        return "critical"
    if priority in {"high"}:
        return "high"
    return "medium"


def _intensity_for(severity: OperatorSeverity) -> float:
    if severity == "critical":
        return 1.0
    if severity == "high":
        return 0.7
    return 0.4


def _emit(
    telemetry_service: object | None,
    event_type: str,
    node_type: str,
    node_id: str,
    intensity: float,
    payload: dict[str, object],
    trace_id: str | None,
) -> None:
    emit = getattr(telemetry_service, "emit", None)
    if not callable(emit):
        return
    try:
        emit(
            VisualTelemetryEvent(
                telemetry_id=f"telemetry-operator-{event_type}-{node_id}-{uuid4().hex}",
                trace_id=trace_id or "operator",
                event_type=cast(Any, event_type),
                node_type=cast(Any, node_type),
                node_id=node_id,
                edge_from=None,
                edge_to=None,
                intensity=intensity,
                payload=payload,
                created_at=datetime.now(UTC),
            )
        )
    except Exception:
        return
