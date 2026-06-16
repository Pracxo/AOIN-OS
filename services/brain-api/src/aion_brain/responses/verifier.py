"""Local response verifier."""

from __future__ import annotations

from datetime import UTC, datetime
from uuid import uuid4

from aion_brain.contracts.responses import (
    ResponseDraft,
    ResponseVerification,
    ResponseVerificationStatus,
    text_has_hidden_markers,
    text_has_secret_markers,
)
from aion_brain.dialogue._shared import authorize, emit_telemetry
from aion_brain.dialogue.repository import DialogueRepository


class ResponseVerifier:
    """Verify response drafts without external calls."""

    def __init__(
        self,
        repository: DialogueRepository,
        policy_adapter: object,
        *,
        telemetry_service: object | None = None,
        belief_service: object | None = None,
        entity_service: object | None = None,
        situation_service: object | None = None,
        state_atom_service: object | None = None,
        capability_awareness_service: object | None = None,
    ) -> None:
        self._repository = repository
        self._policy_adapter = policy_adapter
        self._telemetry_service = telemetry_service
        self._belief_service = belief_service
        self._entity_service = entity_service
        self._situation_service = situation_service
        self._state_atom_service = state_atom_service
        self._capability_awareness_service = capability_awareness_service

    def verify(self, response_id: str) -> ResponseVerification:
        """Verify and persist one response verification record."""

        response = self._repository.get_response(response_id)
        if response is None:
            raise ValueError("response_not_found")
        scope = _scope_from_response(response)
        authorize(
            self._policy_adapter,
            action_type="dialogue.response.verify",
            resource_type="response",
            resource_id=response_id,
            scope=scope,
            trace_id=response.trace_id,
            risk_level="low",
            context={"status": response.status},
        )
        issues = _issues(
            response,
            [
                *self._belief_issues(response, scope),
                *self._entity_issues(response, scope),
                *self._situation_issues(response, scope),
                *self._self_model_issues(response, scope),
            ],
        )
        score = max(0.0, 1.0 - (0.25 * len(issues)))
        status = _verification_status(response, issues)
        verification = ResponseVerification(
            verification_id=f"response-verification-{uuid4().hex}",
            response_id=response.response_id,
            trace_id=response.trace_id,
            status=status,
            grounded=response.grounded,
            policy_ok=not any("policy" in str(issue.get("code", "")) for issue in issues),
            autonomy_ok=not any("autonomy" in str(issue.get("code", "")) for issue in issues),
            approval_required=any("approval_required" in item for item in response.constraints),
            issues=issues,
            score=score,
            metadata={"verified_locally": True},
            created_at=datetime.now(UTC),
        )
        stored = self._repository.save_verification(verification)
        emit_telemetry(
            self._telemetry_service,
            event_type="response_verified",
            node_type="response",
            node_id=response.response_id,
            intensity=0.6,
            trace_id=response.trace_id,
            payload={"owner_scope": scope, "status": stored.status, "score": stored.score},
        )
        if stored.status in {"failed", "blocked"}:
            emit_telemetry(
                self._telemetry_service,
                event_type="response_blocked",
                node_type="response",
                node_id=response.response_id,
                intensity=1.0,
                trace_id=response.trace_id,
                payload={"owner_scope": scope, "issues": [item["code"] for item in issues]},
            )
        if stored.status == "passed" and response.status == "draft":
            self._repository.save_response(
                response.model_copy(update={"status": "verified", "updated_at": datetime.now(UTC)})
            )
        return stored

    def _belief_issues(
        self,
        response: ResponseDraft,
        scope: list[str],
    ) -> list[dict[str, object]]:
        belief_ids = _belief_ids_from_response(response)
        issues: list[dict[str, object]] = []
        get_claim = getattr(self._belief_service, "get_claim", None)
        if not belief_ids or not callable(get_claim):
            return issues
        for belief_id in belief_ids:
            claim = get_claim(belief_id, scope)
            if claim is None:
                issues.append({"code": "belief_ungrounded", "severity": "medium"})
                continue
            status = str(getattr(claim, "status", "unknown"))
            if status == "contradicted":
                issues.append({"code": "belief_contradicted", "severity": "high"})
            elif status == "stale":
                issues.append({"code": "belief_stale", "severity": "medium"})
            if response.metadata.get("require_grounding") is True and not getattr(
                claim,
                "evidence_refs",
                [],
            ):
                issues.append({"code": "belief_ungrounded", "severity": "medium"})
        return issues

    def _self_model_issues(
        self,
        response: ResponseDraft,
        scope: list[str],
    ) -> list[dict[str, object]]:
        issues = _unsafe_self_claim_issues(response.content)
        unsupported = _unsupported_capability_claims(
            response.content,
            self._capability_awareness_service,
            scope,
        )
        for capability_key in unsupported:
            issues.append(
                {
                    "code": "unsupported_capability_claim",
                    "severity": "high",
                    "capability_key": capability_key,
                }
            )
            emit_telemetry(
                self._telemetry_service,
                event_type="unsupported_capability_claim_detected",
                node_type="response",
                node_id=response.response_id,
                intensity=0.9,
                trace_id=response.trace_id,
                payload={"owner_scope": scope, "capability_key": capability_key},
            )
        return issues

    def _situation_issues(
        self,
        response: ResponseDraft,
        scope: list[str],
    ) -> list[dict[str, object]]:
        issues: list[dict[str, object]] = []
        get_situation = getattr(self._situation_service, "get", None)
        situation_id = _situation_id_from_response(response)
        if situation_id and callable(get_situation):
            situation = get_situation(situation_id, scope)
            if situation is None:
                issues.append({"code": "situation_missing", "severity": "medium"})
            elif str(getattr(situation, "status", "")) == "closed":
                issues.append({"code": "situation_closed_as_current", "severity": "medium"})
        get_atom = getattr(self._state_atom_service, "get", None)
        if callable(get_atom):
            for atom_id in _state_atom_ids_from_response(response):
                atom = get_atom(atom_id, scope)
                if atom is None:
                    issues.append({"code": "state_atom_missing", "severity": "medium"})
                    continue
                status = str(getattr(atom, "status", "unknown"))
                if status == "stale":
                    issues.append({"code": "state_atom_stale", "severity": "medium"})
                elif status == "contradicted":
                    issues.append({"code": "state_atom_contradicted", "severity": "high"})
                atom_type = str(getattr(atom, "atom_type", "unknown"))
                if (
                    atom_type == "belief_state"
                    and response.metadata.get("require_grounding") is True
                    and not getattr(atom, "evidence_refs", [])
                ):
                    issues.append({"code": "state_atom_belief_ungrounded", "severity": "medium"})
        return issues

    def _entity_issues(
        self,
        response: ResponseDraft,
        scope: list[str],
    ) -> list[dict[str, object]]:
        entity_ids = _entity_ids_from_response(response)
        issues: list[dict[str, object]] = []
        get_entity = getattr(self._entity_service, "get", None)
        if not entity_ids or not callable(get_entity):
            return issues
        for entity_id in entity_ids:
            entity = get_entity(entity_id, scope)
            if entity is None:
                issues.append({"code": "entity_unresolved", "severity": "medium"})
                continue
            status = str(getattr(entity, "status", "unknown"))
            if status == "merged":
                issues.append({"code": "entity_merged", "severity": "medium"})
            elif status == "archived":
                issues.append({"code": "entity_archived", "severity": "medium"})
            if response.metadata.get("require_grounding") is True and not getattr(
                entity,
                "evidence_refs",
                [],
            ):
                issues.append({"code": "entity_ungrounded", "severity": "medium"})
        return issues


def _issues(
    response: ResponseDraft,
    belief_issues: list[dict[str, object]] | None = None,
) -> list[dict[str, object]]:
    issues: list[dict[str, object]] = []
    if not response.content.strip():
        issues.append({"code": "empty_content", "severity": "high"})
    if text_has_hidden_markers(response.content):
        issues.append({"code": "hidden_reasoning_present", "severity": "critical"})
    if text_has_secret_markers(response.content):
        issues.append({"code": "secret_like_content_present", "severity": "critical"})
    if response.metadata.get("require_grounding") is True and not response.grounded:
        issues.append({"code": "grounding_required_missing", "severity": "high"})
    if response.metadata.get("decision_recommendation") and _claims_decision_executed(
        response.content
    ):
        issues.append({"code": "decision_claimed_execution", "severity": "high"})
    if (
        response.metadata.get("require_grounding") is True
        and response.metadata.get("decision_recommendation")
        and not response.evidence_refs
        and not response.metadata.get("belief_refs")
    ):
        issues.append({"code": "decision_recommendation_ungrounded", "severity": "medium"})
    if response.status == "blocked":
        issues.append({"code": "policy_or_safety_blocked", "severity": "high"})
    if any("autonomy" in item for item in response.constraints):
        issues.append({"code": "autonomy_constraint_present", "severity": "medium"})
    issues.extend(belief_issues or [])
    return issues


def _unsafe_self_claim_issues(content: str) -> list[dict[str, object]]:
    lowered = content.lower()
    issues: list[dict[str, object]] = []
    if any(marker in lowered for marker in ("sentient", "conscious", "self-aware")):
        issues.append({"code": "sentience_claim", "severity": "critical"})
    if any(marker in lowered for marker in ("production ready", "production-ready")):
        issues.append({"code": "production_readiness_claim", "severity": "critical"})
    if any(marker in lowered for marker in ("fully autonomous", "full autonomy")):
        issues.append({"code": "full_autonomy_claim", "severity": "critical"})
    return issues


def _unsupported_capability_claims(
    content: str,
    service: object | None,
    scope: list[str],
) -> list[str]:
    lowered = content.lower()
    checks = {
        "aion.optional.langfuse": ("langfuse",),
        "aion.optional.turbovec": ("turbovec",),
        "aion.optional.graphiti": ("graphiti",),
        "aion.sandbox.execution": ("sandbox execution", "execute sandbox"),
        "aion.model_gateway.external_calls": ("external model", "live model"),
    }
    get_capability = getattr(service, "get_capability", None)
    unsupported: list[str] = []
    for capability_key, markers in checks.items():
        if not any(marker in lowered for marker in markers):
            continue
        if not callable(get_capability):
            unsupported.append(capability_key)
            continue
        try:
            record = get_capability(capability_key, scope)
        except Exception:
            unsupported.append(capability_key)
            continue
        if record is None or getattr(record, "availability", "unknown") != "available":
            unsupported.append(capability_key)
    return unsupported


def _verification_status(
    response: ResponseDraft,
    issues: list[dict[str, object]],
) -> ResponseVerificationStatus:
    if response.status == "blocked":
        return "blocked"
    if any(issue["severity"] == "critical" for issue in issues):
        return "failed"
    if issues:
        return "warning"
    return "passed"


def _scope_from_response(response: ResponseDraft) -> list[str]:
    raw = response.metadata.get("owner_scope") or response.metadata.get("scope")
    if isinstance(raw, list):
        values = [str(item) for item in raw]
        if values:
            return values
    return ["workspace:main"]


def _belief_ids_from_response(response: ResponseDraft) -> list[str]:
    raw = response.metadata.get("belief_refs") or response.metadata.get("belief_ids")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item)]


def _claims_decision_executed(content: str) -> bool:
    lowered = content.lower()
    return "decision" in lowered and any(
        marker in lowered for marker in ("executed", "completed the action", "ran the action")
    )


def _entity_ids_from_response(response: ResponseDraft) -> list[str]:
    raw = response.metadata.get("entity_refs") or response.metadata.get("entity_ids")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item)]


def _situation_id_from_response(response: ResponseDraft) -> str | None:
    raw = response.metadata.get("situation_id")
    return str(raw) if raw else None


def _state_atom_ids_from_response(response: ResponseDraft) -> list[str]:
    raw = response.metadata.get("state_atom_refs") or response.metadata.get("state_atom_ids")
    if not isinstance(raw, list):
        return []
    return [str(item) for item in raw if str(item)]
