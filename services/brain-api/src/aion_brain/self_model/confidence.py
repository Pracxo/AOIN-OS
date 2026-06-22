"""Deterministic confidence calibration."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any, cast
from uuid import uuid4

from aion_brain.contracts.confidence import ConfidenceCalibration, ConfidenceCalibrationRequest
from aion_brain.outcomes._shared import audit_optional, authorize, emit_telemetry
from aion_brain.self_model.repository import SelfModelRepository


class ConfidenceCalibrator:
    """Calibrate confidence deterministically from AION-owned references."""

    def __init__(
        self,
        repository: SelfModelRepository,
        policy_adapter: object,
        *,
        settings: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._settings = settings
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink

    def calibrate(self, request: ConfidenceCalibrationRequest) -> ConfidenceCalibration:
        authorize(
            self._policy_adapter,
            action_type="self_model.confidence.calibrate",
            resource_type="confidence_calibration",
            resource_id=request.source_id,
            scope=_scope_from_metadata(request.metadata),
            trace_id=request.trace_id,
            risk_level="low",
            context={"source_type": request.source_type},
        )
        confidence = _score(request)
        low = float(getattr(self._settings, "confidence_low_threshold", 0.4))
        high = float(getattr(self._settings, "confidence_high_threshold", 0.75))
        confidence_level = (
            "low" if confidence < low else ("high" if confidence >= high else "medium")
        )
        grounding_status = _grounding_status(request)
        disclosures = _disclosures(request, confidence_level, grounding_status)
        clarification = (
            confidence_level == "low" and request.source_type in {"response", "reasoning"}
        ) or (request.require_grounding and grounding_status == "ungrounded")
        verification = (
            confidence_level == "medium"
            and request.source_type == "response"
            and not bool(request.metadata.get("verified"))
        ) or (
            request.source_type in {"decision", "outcome"}
            and not (request.evidence_refs or request.belief_refs)
        )
        calibration = ConfidenceCalibration(
            calibration_id=f"confidence-{uuid4().hex}",
            trace_id=request.trace_id,
            response_id=request.response_id,
            reasoning_id=request.reasoning_id,
            decision_frame_id=request.decision_frame_id,
            source_type=request.source_type,
            source_id=request.source_id,
            confidence=confidence,
            confidence_level=cast(Any, confidence_level),
            grounding_status=cast(Any, grounding_status),
            uncertainty_factors=request.uncertainty_factors,
            required_disclosures=disclosures,
            clarification_recommended=clarification,
            verification_recommended=verification,
            metadata={**request.metadata, "deterministic_calibration": True},
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_confidence_calibration(calibration)
        audit_optional(
            self._audit_sink,
            "confidence_calibrated",
            {"calibration_id": stored.calibration_id, "confidence": stored.confidence},
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="confidence_calibrated",
            node_type="confidence",
            node_id=stored.calibration_id,
            intensity=stored.confidence,
            trace_id=stored.trace_id,
            payload={
                "source_type": stored.source_type,
                "confidence_level": stored.confidence_level,
            },
        )
        return stored

    def calibrate_response(
        self,
        response_id: str,
        *,
        trace_id: str | None = None,
        evidence_refs: list[str] | None = None,
        memory_refs: list[str] | None = None,
        require_grounding: bool = False,
        metadata: dict[str, Any] | None = None,
    ) -> ConfidenceCalibration:
        return self.calibrate(
            ConfidenceCalibrationRequest(
                trace_id=trace_id,
                response_id=response_id,
                source_type="response",
                source_id=response_id,
                evidence_refs=evidence_refs or [],
                memory_refs=memory_refs or [],
                require_grounding=require_grounding,
                metadata=metadata or {},
            )
        )

    def list_calibrations(
        self,
        *,
        trace_id: str | None = None,
        response_id: str | None = None,
        limit: int = 100,
    ) -> list[ConfidenceCalibration]:
        authorize(
            self._policy_adapter,
            action_type="self_model.confidence.read",
            resource_type="confidence_calibration",
            resource_id=response_id or trace_id,
            scope=["workspace:main"],
            risk_level="low",
        )
        return self._repository.list_confidence_calibrations(
            trace_id=trace_id,
            response_id=response_id,
            limit=limit,
        )


def _score(request: ConfidenceCalibrationRequest) -> float:
    score = 0.5
    if request.evidence_refs:
        score += 0.20
    if request.belief_refs:
        score += 0.15
    if request.memory_refs and not request.evidence_refs and not request.belief_refs:
        score += 0.05
    if request.require_grounding and not request.evidence_refs:
        score -= 0.30
    score -= min(0.30, 0.10 * len(request.limitations))
    score -= min(0.25, 0.05 * len(request.uncertainty_factors))
    if request.metadata.get("policy_blocked") or request.metadata.get("autonomy_blocked"):
        score -= 0.20
    if request.metadata.get("verified") is True:
        score += 0.10
    return max(0.0, min(1.0, score))


def _grounding_status(request: ConfidenceCalibrationRequest) -> str:
    if request.evidence_refs:
        return "grounded"
    if request.belief_refs or request.memory_refs:
        return "partially_grounded"
    if request.require_grounding:
        return "ungrounded"
    return "not_applicable"


def _disclosures(
    request: ConfidenceCalibrationRequest,
    confidence_level: str,
    grounding_status: str,
) -> list[str]:
    values: list[str] = []
    if grounding_status == "ungrounded":
        values.append("ungrounded_response")
    if confidence_level == "low":
        values.append("low_confidence")
    if request.limitations:
        values.append("optional_adapter_unavailable")
    if request.metadata.get("approval_required"):
        values.append("approval_required")
    if request.metadata.get("dry_run_only"):
        values.append("dry_run_only")
    return list(dict.fromkeys(values))


def _scope_from_metadata(metadata: dict[str, Any]) -> list[str]:
    raw = metadata.get("owner_scope") or metadata.get("scope") or metadata.get("security_scope")
    if isinstance(raw, list) and raw:
        return [str(item) for item in raw]
    return ["workspace:main"]
