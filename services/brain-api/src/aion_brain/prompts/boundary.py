"""Prompt boundary and context guard checks."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contracts.prompts import (
    PromptBoundaryCheck,
    PromptInjectionFinding,
    PromptPacket,
    PromptSection,
)
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.prompts.audit import record_prompt_audit
from aion_brain.prompts.injection_detector import PromptInjectionDetector


class PromptBoundaryChecker:
    """Run deterministic prompt boundary checks."""

    def __init__(
        self,
        repository: object,
        policy_adapter: object | None,
        *,
        detector: PromptInjectionDetector | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        settings: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._detector = detector or PromptInjectionDetector()
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._settings = settings
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> PromptBoundaryChecker:
        return PromptBoundaryChecker(
            self._repository,
            self._policy_adapter,
            detector=self._detector,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            settings=self._settings,
            actor_context=actor_context,
        )

    def check_sections(
        self,
        sections: list[PromptSection],
        *,
        scope: list[str],
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        created_by: str | None = None,
    ) -> PromptBoundaryCheck:
        """Check prompt sections and persist the boundary result."""

        authorize(
            self._policy_adapter,
            action_type="prompt.boundary.check",
            resource_type="prompt_packet",
            resource_id=prompt_packet_id,
            scope=scope,
            trace_id=trace_id or self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="medium",
        )
        warnings: list[dict[str, Any]] = []
        constraints: list[str] = []
        blocked_sections: list[str] = []
        findings = self._detector.detect_in_sections(
            sections,
            trace_id=trace_id or self._actor_context.trace_id,
            prompt_packet_id=prompt_packet_id,
        )
        if not any(section.section_type == "system_boundary" for section in sections):
            warnings.append(
                {"code": "missing_system_boundary", "message": "System boundary missing."}
            )
            constraints.append("system_boundary_required")
        for section in sections:
            if section.section_type == "memory" and section.trust_level != "memory_recall":
                warnings.append({"code": "memory_trust_mismatch", "section_id": section.section_id})
                constraints.append("memory_sections_are_recall_not_truth")
            if section.section_type == "belief" and not section.metadata.get("belief_status"):
                warnings.append({"code": "belief_status_missing", "section_id": section.section_id})
                constraints.append("belief_sections_need_status_metadata")
        block_high = bool(getattr(self._settings, "prompt_injection_block_high_severity", True))
        severe = [finding for finding in findings if finding.severity in {"high", "critical"}]
        if block_high and severe:
            blocked_sections = [
                finding.source_id or finding.source_type for finding in severe if finding.source_id
            ]
            constraints.append("high_severity_prompt_injection_blocked")
        safe = not blocked_sections and not any(
            finding.severity == "critical" for finding in findings
        )
        status = "passed"
        if not safe:
            status = "blocked"
        elif findings or warnings:
            status = "warning"
        score = max(0.0, 1.0 - (0.25 * len(severe)) - (0.05 * len(warnings)))
        check = PromptBoundaryCheck(
            boundary_check_id=f"prompt-boundary-{uuid4().hex}",
            trace_id=trace_id or self._actor_context.trace_id,
            prompt_packet_id=prompt_packet_id,
            status=status,  # type: ignore[arg-type]
            safe=safe,
            injection_findings=findings,
            blocked_sections=blocked_sections,
            warnings=warnings,
            constraints=sorted(set(constraints)),
            score=score,
            metadata={"section_count": len(sections), "deterministic": True},
            created_by=created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
        )
        self._persist_findings(findings)
        saved = self._save_check(check)
        emit_telemetry(
            self._telemetry_service,
            event_type="prompt_boundary_checked",
            node_type="prompt_boundary",
            node_id=saved.boundary_check_id,
            trace_id=saved.trace_id,
            intensity=0.7 if saved.safe else 0.95,
            payload={"status": saved.status, "safe": saved.safe, "score": saved.score},
        )
        for finding in findings:
            emit_telemetry(
                self._telemetry_service,
                event_type="prompt_injection_detected",
                node_type="prompt_injection",
                node_id=finding.injection_finding_id,
                trace_id=finding.trace_id,
                intensity=0.9 if finding.severity in {"high", "critical"} else 0.5,
                payload={"severity": finding.severity, "finding_type": finding.finding_type},
            )
        record_prompt_audit(
            self._audit_sink,
            action_type="prompt.boundary.check",
            resource_type="prompt_boundary",
            resource_id=saved.boundary_check_id,
            event_type="prompt_boundary_checked",
            trace_id=saved.trace_id,
            actor_context=self._actor_context,
            payload={"status": saved.status, "safe": saved.safe, "score": saved.score},
            outcome="completed" if saved.safe else "blocked",
        )
        return saved

    def check_packet(self, packet: PromptPacket) -> PromptBoundaryCheck:
        """Check a compiled packet's sections."""

        return self.check_sections(
            packet.sections,
            scope=packet.owner_scope,
            trace_id=packet.trace_id,
            prompt_packet_id=packet.prompt_packet_id,
            created_by=packet.created_by,
        )

    def get_check(self, boundary_check_id: str) -> PromptBoundaryCheck | None:
        get_check = getattr(self._repository, "get_boundary_check", None)
        result = get_check(boundary_check_id) if callable(get_check) else None
        return result if isinstance(result, PromptBoundaryCheck) else None

    def list_injection_findings(
        self,
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PromptInjectionFinding]:
        """List prompt injection findings after read authorization."""

        scope = self._actor_context.security_scope or ["workspace:main"]
        authorize(
            self._policy_adapter,
            action_type="prompt.injection.read",
            resource_type="prompt_injection",
            resource_id=prompt_packet_id or trace_id,
            scope=scope,
            trace_id=self._actor_context.trace_id,
            actor_id=self._actor_context.actor_id,
            workspace_id=self._actor_context.workspace_id,
            risk_level="low",
        )
        list_findings = getattr(self._repository, "list_injection_findings", None)
        if not callable(list_findings):
            return []
        result = list_findings(
            trace_id=trace_id,
            prompt_packet_id=prompt_packet_id,
            severity=severity,
            status=status,
            limit=limit,
        )
        return [finding for finding in result if isinstance(finding, PromptInjectionFinding)]

    def _save_check(self, check: PromptBoundaryCheck) -> PromptBoundaryCheck:
        save = getattr(self._repository, "save_boundary_check", None)
        result = save(check) if callable(save) else check
        return result if isinstance(result, PromptBoundaryCheck) else check

    def _persist_findings(self, findings: list[PromptInjectionFinding]) -> None:
        save = getattr(self._repository, "save_injection_finding", None)
        if not callable(save):
            return
        for finding in findings:
            try:
                save(finding)
            except Exception:
                continue


__all__ = ["PromptBoundaryChecker"]
