"""Open Policy Agent adapter boundary."""

from datetime import UTC, datetime
from uuid import uuid4

import httpx

from aion_brain.audit_integrity.ledger import record_audit_event
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.policy_catalog import OPAStatus

OPA_DECISION_PATH = "/v1/data/aion/brain/decision"


class OPAAdapter:
    """Adapter boundary for Open Policy Agent.

    This is an adapter boundary. AION public contracts must not depend on the
    external framework.
    """

    def __init__(
        self,
        opa_url: str,
        *,
        timeout_seconds: float = 1.0,
        transport: httpx.BaseTransport | None = None,
    ) -> None:
        self._opa_url = opa_url.rstrip("/")
        self._timeout_seconds = timeout_seconds
        self._transport = transport
        self._audit_sink: object | None = None

    def set_audit_sink(self, audit_sink: object | None) -> None:
        """Attach audit sink after kernel assembly."""
        self._audit_sink = audit_sink

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        """Authorize a Brain action through OPA, failing closed on errors."""
        try:
            with httpx.Client(timeout=self._timeout_seconds, transport=self._transport) as client:
                response = client.post(
                    f"{self._opa_url}{OPA_DECISION_PATH}",
                    json={"input": request.model_dump(mode="json")},
                )
                response.raise_for_status()
                result = response.json()["result"]
            decision = _decision_from_result(request, result)
        except Exception:
            decision = deny_decision(request, reason="policy_engine_unavailable")
        self._record_decision(request, decision)
        return decision

    def status(self) -> OPAStatus:
        """Return OPA availability status without crashing callers."""
        try:
            with httpx.Client(timeout=self._timeout_seconds, transport=self._transport) as client:
                response = client.get(f"{self._opa_url}/health")
                response.raise_for_status()
            return OPAStatus(
                available=True,
                url=self._opa_url,
                policy_loaded=True,
                decision_path=OPA_DECISION_PATH,
                reason=None,
                checked_at=datetime.now(UTC),
            )
        except Exception as exc:
            return OPAStatus(
                available=False,
                url=self._opa_url,
                policy_loaded=False,
                decision_path=OPA_DECISION_PATH,
                reason=str(exc) or "opa_unavailable",
                checked_at=datetime.now(UTC),
            )

    def _record_decision(self, request: PolicyRequest, decision: PolicyDecision) -> None:
        if request.action_type.startswith("audit."):
            return
        record_audit_event(
            self._audit_sink,
            action_type="policy.authorize",
            resource_type=request.resource_type,
            resource_id=request.resource_id,
            event_type="policy_decision_generated",
            outcome="allowed" if decision.allow else "denied",
            source_component="policy_adapter",
            trace_id=request.trace_id,
            actor_id=request.actor_id,
            workspace_id=request.workspace_id,
            risk_level=request.risk_level,
            policy_decision_id=decision.decision_id,
            payload={
                "action_type": request.action_type,
                "allow": decision.allow,
                "approval_required": decision.approval_required,
                "reason": decision.reason,
            },
        )


def _decision_from_result(request: PolicyRequest, result: object) -> PolicyDecision:
    if not isinstance(result, dict):
        return deny_decision(request, reason="policy_engine_unavailable")

    try:
        constraints = result.get("constraints", [])
        if not isinstance(constraints, list) or not all(
            isinstance(item, str) for item in constraints
        ):
            constraints = ["invalid_policy_constraints"]

        return PolicyDecision(
            decision_id=f"decision-{uuid4().hex}",
            trace_id=request.trace_id or "",
            allow=bool(result.get("allow", False)),
            approval_required=bool(result.get("approval_required", False)),
            reason=str(result.get("reason", "policy_engine_unavailable")),
            constraints=constraints,
            audit_level=str(result.get("audit_level", "high")),
        )
    except Exception:
        return deny_decision(request, reason="policy_engine_unavailable")


def deny_decision(request: PolicyRequest, *, reason: str) -> PolicyDecision:
    """Return a fail-closed policy decision."""
    return PolicyDecision(
        decision_id=f"decision-{uuid4().hex}",
        trace_id=request.trace_id or "",
        allow=False,
        approval_required=False,
        reason=reason,
        constraints=["fail_closed"],
        audit_level="high",
    )
