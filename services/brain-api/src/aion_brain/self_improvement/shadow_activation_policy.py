"""Policy service for disabled shadow activation decisions."""

from __future__ import annotations

import json
from collections.abc import Callable
from pathlib import Path
from typing import Any, Protocol

from aion_brain.contracts.self_improvement_shadow import canonical_shadow_fingerprint
from aion_brain.contracts.self_improvement_shadow_activation import (
    MAXIMUM_EVIDENCE_BUNDLE_BYTES,
    ShadowActivationApprovalBinding,
    ShadowActivationAuditEvent,
    ShadowActivationBudgetDecision,
    ShadowActivationCandidate,
    ShadowActivationCurrentFacts,
    ShadowActivationDeactivationDecision,
    ShadowActivationDecisionOutcome,
    ShadowActivationDiagnostics,
    ShadowActivationEvaluationBundle,
    ShadowActivationEvidenceBundle,
    ShadowActivationHealthSnapshot,
    ShadowActivationMonitoringDecision,
    ShadowActivationOperatorReviewItem,
    ShadowActivationProvenanceRecord,
    ShadowActivationRequest,
    ShadowActivationResourceUsage,
    build_current_facts_from_request,
    evaluate_shadow_activation_budget,
    evaluate_shadow_activation_deactivation,
    evaluate_shadow_activation_health,
    require_activation_identifier,
    require_fingerprint,
    utc_now,
    validate_activation_candidate,
    validate_shadow_activation_approval,
    validate_shadow_activation_output_boundary,
)
from aion_brain.self_improvement.shadow_evidence import ShadowEvidenceBundle


class ShadowActivationEvidenceAdapter(Protocol):
    """Read-only evidence adapter contract."""

    def load_evidence_bundle(self) -> ShadowEvidenceBundle:
        """Load one exact redacted shadow evidence bundle."""


class InMemoryShadowActivationEvidenceAdapter:
    """Read-only adapter over a caller-supplied immutable bundle."""

    def __init__(
        self,
        *,
        bundle: ShadowEvidenceBundle,
        expected_bundle_fingerprint: str,
    ) -> None:
        self._bundle = bundle
        self._expected_bundle_fingerprint = require_fingerprint(
            expected_bundle_fingerprint,
            "expected_bundle_fingerprint",
        )

    def load_evidence_bundle(self) -> ShadowEvidenceBundle:
        """Return the supplied bundle after exact fingerprint validation."""

        observed = shadow_evidence_bundle_fingerprint(self._bundle)
        if observed != self._expected_bundle_fingerprint:
            raise ValueError("activation evidence bundle fingerprint mismatch")
        return self._bundle


class ExplicitLocalShadowEvidenceBundleAdapter:
    """Read-only adapter over one explicit local evidence file."""

    def __init__(
        self,
        *,
        path: Path,
        repository_root: Path,
        expected_bundle_fingerprint: str,
        maximum_bytes: int = MAXIMUM_EVIDENCE_BUNDLE_BYTES,
    ) -> None:
        self._path = path
        self._repository_root = repository_root
        self._expected_bundle_fingerprint = require_fingerprint(
            expected_bundle_fingerprint,
            "expected_bundle_fingerprint",
        )
        if maximum_bytes < 1 or maximum_bytes > MAXIMUM_EVIDENCE_BUNDLE_BYTES:
            raise ValueError("activation evidence bundle byte limit is out of bounds")
        self._maximum_bytes = maximum_bytes

    def load_evidence_bundle(self) -> ShadowEvidenceBundle:
        """Validate and load the explicit local evidence bundle."""

        path = self._validate_path()
        size = path.stat().st_size
        if size > self._maximum_bytes:
            raise ValueError("activation evidence bundle is too large")
        raw = path.read_bytes()
        try:
            text = raw.decode("utf-8")
        except UnicodeDecodeError as exc:
            raise ValueError("activation evidence bundle must be UTF-8") from exc
        try:
            payload = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError("activation evidence bundle must be JSON") from exc
        if not isinstance(payload, dict):
            raise ValueError("activation evidence bundle must be a JSON object")
        _scan_operator_material(payload)
        bundle = ShadowEvidenceBundle.model_validate(payload)
        observed = shadow_evidence_bundle_fingerprint(bundle)
        if observed != self._expected_bundle_fingerprint:
            raise ValueError("activation evidence bundle fingerprint mismatch")
        return bundle

    def _validate_path(self) -> Path:
        path = self._path
        text = str(path)
        if "://" in text or text.startswith("//"):
            raise ValueError("activation evidence path must be local")
        if "$" in text or text.startswith("~"):
            raise ValueError("activation evidence path cannot require expansion")
        if not path.is_absolute():
            raise ValueError("activation evidence path must be absolute")
        if ".." in path.parts:
            raise ValueError("activation evidence path cannot contain traversal")
        if any(part.startswith(".") for part in path.parts if part not in {"/"}):
            raise ValueError("activation evidence path cannot be hidden")
        for candidate in (path, *path.parents):
            if candidate.exists() and candidate.is_symlink():
                raise ValueError("activation evidence path cannot use symlinks")
        resolved = path.resolve(strict=True)
        repository_root = self._repository_root.resolve(strict=True)
        if resolved == repository_root or repository_root in resolved.parents:
            raise ValueError("activation evidence path cannot be inside the repository")
        if not resolved.is_file():
            raise ValueError("activation evidence path must be a regular file")
        return resolved


class ShadowActivationPolicyService:
    """Evaluate disabled control-plane decisions with injected collaborators."""

    def __init__(
        self,
        *,
        evidence_adapter: ShadowActivationEvidenceAdapter,
        repository_root: Path,
        clock: Callable[[], Any] = utc_now,
        id_factory: Callable[[str], str] | None = None,
    ) -> None:
        self._evidence_adapter = evidence_adapter
        self._repository_root = repository_root
        self._clock = clock
        self._id_factory = id_factory or (lambda label: f"shadow-activation-{label}")

    def evaluate(
        self,
        *,
        candidate: ShadowActivationCandidate,
        request: ShadowActivationRequest,
        approval: ShadowActivationApprovalBinding | None = None,
        current_facts: ShadowActivationCurrentFacts | None = None,
        resource_usage: ShadowActivationResourceUsage | None = None,
        health_snapshot: ShadowActivationHealthSnapshot | None = None,
        current_state: str = "drafted",
    ) -> ShadowActivationEvaluationBundle:
        """Evaluate one disabled activation-control-plane decision."""

        now = self._clock()
        candidate_validation = validate_activation_candidate(candidate, now=now)
        output_validation = validate_shadow_activation_output_boundary(
            request.output_boundary,
            repository_root=self._repository_root,
        )
        usage = resource_usage or ShadowActivationResourceUsage()
        budget_decision = evaluate_shadow_activation_budget(usage, request.resource_budget)
        self._evidence_adapter.load_evidence_bundle()
        snapshot = health_snapshot or ShadowActivationHealthSnapshot(
            activation_candidate_id=candidate.activation_candidate_id,
            observed_at=now,
        )
        monitoring_decision = evaluate_shadow_activation_health(
            snapshot,
            request.monitoring_plan,
            activation_window_end=request.activation_window_end,
            maximum_runs=request.maximum_runs,
            now=now,
        )
        deactivation_decision = evaluate_shadow_activation_deactivation(
            health_decision=monitoring_decision,
            deactivation_plan=request.deactivation_plan,
            now=now,
            decision_id=self._id_factory("deactivation"),
        )
        approval_validation = None
        if approval is not None:
            approval_validation = validate_shadow_activation_approval(
                approval=approval,
                candidate=candidate,
                request=request,
                current_facts=current_facts or build_current_facts_from_request(request),
                now=now,
            )
        outcome = _policy_outcome(
            candidate_validation=candidate_validation.valid,
            candidate_expired=candidate_validation.expired,
            request_valid=output_validation.valid,
            budget_decision=budget_decision,
            monitoring_decision=monitoring_decision,
            approval_validation=approval_validation,
            current_state=current_state,
        )
        reason_codes = _reason_codes_for_outcome(
            outcome,
            budget_decision,
            monitoring_decision,
            approval_validation,
        )
        review_item = _operator_review_item(
            candidate=candidate,
            request=request,
            current_state=current_state,
            outcome=outcome,
            candidate_valid=candidate_validation.valid,
            approval_valid=approval_validation.valid if approval_validation else False,
            budget_decision=budget_decision,
            monitoring_decision=monitoring_decision,
            deactivation_decision=deactivation_decision,
            reason_codes=reason_codes,
            created_at=now,
            review_item_id=self._id_factory("review"),
        )
        diagnostics = ShadowActivationDiagnostics(
            diagnostics_id=self._id_factory("diagnostics"),
            activation_candidate_id=candidate.activation_candidate_id,
            activation_request_id=request.activation_request_id,
            candidate_valid=candidate_validation.valid,
            request_valid=output_validation.valid,
            approval_valid=approval_validation.valid if approval_validation else False,
            budget_within_limits=budget_decision.within_budget,
            monitoring_passed=monitoring_decision.monitoring_passed,
            deactivation_required=deactivation_decision.triggered,
            created_at=now,
        )
        provenance = ShadowActivationProvenanceRecord(
            provenance_record_id=self._id_factory("provenance"),
            activation_candidate_id=candidate.activation_candidate_id,
            activation_request_id=request.activation_request_id,
            evidence_fingerprints={
                "candidate": candidate.fingerprint,
                "request": request.fingerprint,
                "budget": budget_decision.fingerprint,
                "monitoring": monitoring_decision.fingerprint,
                "deactivation": deactivation_decision.fingerprint,
            },
            created_at=now,
        )
        audit_event = ShadowActivationAuditEvent(
            audit_event_id=self._id_factory("audit"),
            activation_candidate_id=candidate.activation_candidate_id,
            activation_request_id=request.activation_request_id,
            event_type="activation_policy_evaluated",
            decision_outcome=outcome,
            reason_codes=reason_codes,
            created_at=now,
        )
        evidence = ShadowActivationEvidenceBundle(
            activation_candidate_id=candidate.activation_candidate_id,
            activation_request_id=request.activation_request_id,
            decision_outcome=outcome,
            audit_events=(audit_event,),
            provenance=provenance,
            diagnostics=diagnostics,
            operator_review_item=review_item,
            created_at=now,
        )
        return ShadowActivationEvaluationBundle(
            decision_outcome=outcome,
            candidate_validation=candidate_validation,
            approval_validation=approval_validation,
            budget_decision=budget_decision,
            monitoring_decision=monitoring_decision,
            deactivation_decision=deactivation_decision,
            evidence_bundle=evidence,
            reason_codes=reason_codes,
        )


def shadow_evidence_bundle_fingerprint(bundle: ShadowEvidenceBundle) -> str:
    """Return the canonical fingerprint for AION-178 shadow evidence."""

    return canonical_shadow_fingerprint(bundle.model_dump(mode="python"))


def _policy_outcome(
    *,
    candidate_validation: bool,
    candidate_expired: bool,
    request_valid: bool,
    budget_decision: ShadowActivationBudgetDecision,
    monitoring_decision: ShadowActivationMonitoringDecision,
    approval_validation: Any,
    current_state: str,
) -> ShadowActivationDecisionOutcome:
    if current_state == "expired":
        return "expired"
    if current_state == "revoked":
        return "revoked"
    if current_state == "archived":
        return "archived"
    if candidate_expired:
        return "expired"
    if not candidate_validation or not request_valid or not budget_decision.within_budget:
        return "candidate_invalid"
    if monitoring_decision.deactivation_required:
        return "simulation_failed"
    if approval_validation is None:
        return "approval_required"
    if approval_validation.expired:
        return "expired"
    if not approval_validation.valid:
        return "approval_invalid"
    return "simulation_ready"


def _reason_codes_for_outcome(
    outcome: ShadowActivationDecisionOutcome,
    budget_decision: ShadowActivationBudgetDecision,
    monitoring_decision: ShadowActivationMonitoringDecision,
    approval_validation: Any,
) -> tuple[str, ...]:
    codes: list[str] = ["activation_runtime_disabled", "activation_scope_control_plane_only"]
    codes.extend(budget_decision.reason_codes)
    codes.append(
        "activation_monitoring_passed"
        if monitoring_decision.monitoring_passed
        else "activation_monitoring_breached"
    )
    if monitoring_decision.deactivation_required:
        codes.append("activation_deactivation_required")
    else:
        codes.append("activation_deactivation_not_required")
    if approval_validation is None:
        codes.append("activation_approval_required")
    else:
        codes.extend(approval_validation.reason_codes)
    if outcome == "simulation_ready":
        codes.append("activation_simulation_ready")
    if outcome == "candidate_invalid":
        codes.append("activation_candidate_invalid")
    if outcome == "simulation_failed":
        codes.append("activation_simulation_failed")
    if outcome == "expired":
        codes.append("activation_candidate_expired")
    return tuple(dict.fromkeys(codes))


def _operator_review_item(
    *,
    candidate: ShadowActivationCandidate,
    request: ShadowActivationRequest,
    current_state: str,
    outcome: ShadowActivationDecisionOutcome,
    candidate_valid: bool,
    approval_valid: bool,
    budget_decision: ShadowActivationBudgetDecision,
    monitoring_decision: ShadowActivationMonitoringDecision,
    deactivation_decision: ShadowActivationDeactivationDecision,
    reason_codes: tuple[str, ...],
    created_at: Any,
    review_item_id: str,
) -> ShadowActivationOperatorReviewItem:
    return ShadowActivationOperatorReviewItem(
        review_item_id=require_activation_identifier(review_item_id, "review_item_id"),
        activation_candidate_id=candidate.activation_candidate_id,
        activation_request_id=request.activation_request_id,
        current_state=current_state,  # type: ignore[arg-type]
        decision_outcome=outcome,
        candidate_validation_summary="candidate valid" if candidate_valid else "candidate invalid",
        approval_validation_summary="approval valid" if approval_valid else "approval required",
        budget_summary="budget satisfied" if budget_decision.within_budget else "budget exceeded",
        monitoring_summary=(
            "monitoring passed"
            if monitoring_decision.monitoring_passed
            else "monitoring breached"
        ),
        deactivation_summary=(
            "deactivation required"
            if deactivation_decision.triggered
            else "deactivation not required"
        ),
        evidence_fingerprints={
            "candidate": candidate.fingerprint,
            "request": request.fingerprint,
            "budget": budget_decision.fingerprint,
            "monitoring": monitoring_decision.fingerprint,
            "deactivation": deactivation_decision.fingerprint,
        },
        reason_codes=reason_codes,
        created_at=created_at,
        expires_at=request.activation_candidate.expires_at,
    )


def _scan_operator_material(payload: dict[str, Any]) -> None:
    for key in (
        "observations",
        "evaluation_summary",
        "failure_patterns",
        "hypotheses",
        "regression_test_proposals",
        "shadow_proposals",
        "operator_review_items",
    ):
        if key in payload:
            _scan_value(payload[key])


def _scan_value(value: Any) -> None:
    if isinstance(value, str):
        _reject_protected_text(value)
    elif isinstance(value, dict):
        for item in value.values():
            _scan_value(item)
    elif isinstance(value, list | tuple):
        for item in value:
            _scan_value(item)
    elif isinstance(value, bytes | bytearray | memoryview) or callable(value):
        raise ValueError("activation evidence bundle contains prohibited material")


def _reject_protected_text(value: str) -> None:
    try:
        from aion_brain.contracts.self_improvement_shadow import validate_shadow_text

        validate_shadow_text(value, field_name="activation evidence text", max_length=4096)
    except ValueError as exc:
        raise ValueError("activation evidence bundle contains prohibited material") from exc


__all__ = [
    "ExplicitLocalShadowEvidenceBundleAdapter",
    "InMemoryShadowActivationEvidenceAdapter",
    "ShadowActivationEvidenceAdapter",
    "ShadowActivationPolicyService",
    "shadow_evidence_bundle_fingerprint",
]
