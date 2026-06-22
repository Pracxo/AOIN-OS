"""AION Memory Fabric service."""

from aion_brain.contracts.memory import MemoryRecord, MemoryRetrievalRequest, MemoryType
from aion_brain.contracts.memory_governance import (
    MemoryGovernanceDecision,
    MemoryGovernanceEvaluationRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.memory.base import LexicalMemoryAdapter
from aion_brain.policy.base import PolicyAdapter


class MemoryPolicyDenied(Exception):
    """Raised when policy denies a memory action."""

    def __init__(self, decision: PolicyDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class MemoryGovernanceDenied(Exception):
    """Raised when memory governance denies a memory action."""

    def __init__(self, decision: MemoryGovernanceDecision) -> None:
        super().__init__(decision.reason)
        self.decision = decision


class PostgresMemoryService:
    """Canonical memory service with policy checks and lexical retrieval."""

    def __init__(
        self,
        memory_adapter: LexicalMemoryAdapter,
        policy_adapter: PolicyAdapter,
        governance_engine: object | None = None,
    ) -> None:
        self._memory_adapter = memory_adapter
        self._policy_adapter = policy_adapter
        self._governance_engine = governance_engine

    def set_governance_engine(self, governance_engine: object | None) -> None:
        """Attach memory governance after composition when needed."""
        self._governance_engine = governance_engine

    def create(self, record: MemoryRecord) -> MemoryRecord:
        """Authorize and store a memory record."""
        self._ensure_allowed(
            PolicyRequest(
                request_id=f"memory-write-{record.memory_id}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="memory.write",
                resource_type="memory",
                resource_id=record.memory_id,
                risk_level=_risk_from_sensitivity(record.sensitivity),
                approval_present=False,
                requested_permissions=[],
                security_scope=record.owner_scope,
                context={"memory_type": record.memory_type},
            )
        )
        governance = self._evaluate_governance(record, "memory.write", record.owner_scope)
        if governance.decision in {"deny", "require_approval", "forget", "expire"}:
            raise MemoryGovernanceDenied(governance)
        governed = _annotate_record(record, governance)
        self._memory_adapter.remember(governed)
        return governed

    def get(self, memory_id: str) -> MemoryRecord | None:
        """Return a memory record by ID if the adapter supports direct lookup."""
        get_record = getattr(self._memory_adapter, "get", None)
        if not callable(get_record):
            return None
        result = get_record(memory_id)
        if result is None or isinstance(result, MemoryRecord):
            return result
        raise TypeError("memory adapter get() returned a non-MemoryRecord value")

    def retrieve(self, request: MemoryRetrievalRequest) -> list[MemoryRecord]:
        """Authorize and retrieve memories using deterministic recall."""
        self._ensure_allowed(
            PolicyRequest(
                request_id="memory-retrieve",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="memory.retrieve",
                resource_type="memory",
                resource_id=None,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=request.scope,
                context={"memory_types": request.memory_types},
            )
        )
        records = self._memory_adapter.retrieve(
            request.query,
            request.scope,
            limit=request.limit,
            memory_types=request.memory_types,
        )
        governed: list[MemoryRecord] = []
        for record in records:
            decision = self._evaluate_governance(
                record,
                "memory.retrieve",
                request.scope,
                context={"retrieval_query": request.query},
            )
            if decision.decision in {"deny", "expire", "forget"}:
                continue
            governed.append(_annotate_record(record, decision))
        return governed

    def delete(self, memory_id: str) -> bool:
        """Authorize and soft-delete a memory record."""
        self._ensure_allowed(
            PolicyRequest(
                request_id=f"memory-delete-{memory_id}",
                trace_id=None,
                actor_id=None,
                workspace_id=None,
                action_type="memory.write",
                resource_type="memory",
                resource_id=memory_id,
                risk_level="low",
                approval_present=False,
                requested_permissions=[],
                security_scope=[],
                context={"operation": "soft_delete"},
            )
        )
        return self._memory_adapter.forget(memory_id)

    def update_metadata(self, memory_id: str, metadata: dict[str, object]) -> MemoryRecord | None:
        """Update metadata through the canonical memory adapter when available."""
        update_metadata = getattr(self._memory_adapter, "update_metadata", None)
        if not callable(update_metadata):
            return None
        result = update_metadata(memory_id, metadata)
        if result is None or isinstance(result, MemoryRecord):
            return result
        raise TypeError("memory adapter update_metadata() returned a non-MemoryRecord value")

    def expire(self, memory_id: str) -> bool:
        """Expire a memory record without hard deletion."""
        expire = getattr(self._memory_adapter, "expire", None)
        if callable(expire):
            return bool(expire(memory_id))
        record = self.get(memory_id)
        if record is None:
            return False
        updated = self.update_metadata(
            memory_id,
            {**record.metadata, "governance_status": "expired"},
        )
        return updated is not None

    def list_active(
        self,
        scope: list[str],
        *,
        limit: int = 100,
        memory_types: list[MemoryType] | None = None,
    ) -> list[MemoryRecord]:
        """List active memory records when the adapter supports it."""
        list_active = getattr(self._memory_adapter, "list_active", None)
        if not callable(list_active):
            return []
        result = list_active(scope, limit=limit, memory_types=memory_types)
        if isinstance(result, list) and all(isinstance(item, MemoryRecord) for item in result):
            return result
        raise TypeError("memory adapter list_active() returned non-MemoryRecord values")

    def _ensure_allowed(self, request: PolicyRequest) -> None:
        decision = self._policy_adapter.authorize(request)
        if not decision.allow:
            raise MemoryPolicyDenied(decision)

    def _evaluate_governance(
        self,
        record: MemoryRecord,
        action_type: str,
        owner_scope: list[str],
        context: dict[str, object] | None = None,
    ) -> MemoryGovernanceDecision:
        evaluate = getattr(self._governance_engine, "evaluate", None)
        if not callable(evaluate):
            return MemoryGovernanceDecision(
                governance_decision_id=f"memory-governance-disabled-{record.memory_id}",
                trace_id=None,
                memory_id=record.memory_id,
                rule_ids=[],
                decision="allow",
                reason="memory_governance_not_configured",
                constraints=[],
                metadata={"action_type": action_type},
                created_at=None,
            )
        result = evaluate(
            MemoryGovernanceEvaluationRequest(
                trace_id=None,
                memory=record,
                action_type=action_type,  # type: ignore[arg-type]
                owner_scope=owner_scope,
                context=context or {},
            )
        )
        if isinstance(result, MemoryGovernanceDecision):
            return result
        raise TypeError("memory governance evaluate() returned a non-decision value")


def _risk_from_sensitivity(sensitivity: str) -> str:
    normalized = sensitivity.lower()
    if normalized in {"high", "critical"}:
        return "high"
    if normalized == "medium":
        return "medium"
    return "low"


def _annotate_record(
    record: MemoryRecord,
    decision: MemoryGovernanceDecision,
) -> MemoryRecord:
    if decision.decision == "allow" and not decision.rule_ids:
        return record
    return record.model_copy(
        update={
            "metadata": {
                **record.metadata,
                "governance_decision_id": decision.governance_decision_id,
                "governance_decision": decision.decision,
                "governance_constraints": decision.constraints,
                "recall_only": True,
            }
        }
    )
