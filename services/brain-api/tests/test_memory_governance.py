"""Memory governance tests."""

from datetime import UTC, datetime, timedelta
from typing import Any

import pytest
from fastapi.testclient import TestClient
from pydantic import ValidationError

from aion_brain.api.memory_governance import (
    get_memory_compaction_service,
    get_memory_conflict_service,
    get_memory_decay_service,
    get_memory_forgetting_service,
    get_memory_governance_engine,
    get_memory_retention_service,
)
from aion_brain.config import Settings
from aion_brain.contracts.approvals import ApprovalCreateRequest
from aion_brain.contracts.memory import MemoryRecord, MemoryRetrievalRequest
from aion_brain.contracts.memory_governance import (
    ForgetMemoryRequest,
    MemoryCompactionRequest,
    MemoryConflictResolutionRequest,
    MemoryConflictScanRequest,
    MemoryGovernanceEvaluationRequest,
    MemoryGovernanceRule,
    MemoryRetentionSweepRequest,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest
from aion_brain.contracts.scopes import ActorContext
from aion_brain.identity.dev_auth import get_actor_context
from aion_brain.main import app
from aion_brain.memory.in_memory_adapter import InMemorySemanticMemoryAdapter
from aion_brain.memory.service import MemoryGovernanceDenied, PostgresMemoryService
from aion_brain.memory_governance.compaction import MemoryCompactionService
from aion_brain.memory_governance.conflicts import MemoryConflictService
from aion_brain.memory_governance.decay import MemoryDecayService
from aion_brain.memory_governance.engine import MemoryGovernanceEngine
from aion_brain.memory_governance.forgetting import MemoryForgettingService
from aion_brain.memory_governance.repository import MemoryGovernanceRepository
from aion_brain.memory_governance.retention import MemoryRetentionService
from aion_brain.retrieval.router import RetrievalRouter
from tests.test_risk_guardrail_approval_api import approval_request


def test_governance_rule_validates_safe_generic_metadata() -> None:
    """Governance contracts reject secret-like and domain-specific rule payloads."""
    with pytest.raises(ValidationError):
        rule(metadata={"api_key": "hidden"})

    with pytest.raises(ValidationError):
        rule(name="finance specific rule")


def test_engine_denies_matching_retrieval_gate() -> None:
    """GovernanceEngine selects deterministic deny decisions."""
    engine, _repository = make_engine()
    engine.create_rule(
        rule(
            governance_rule_id="rule-deny",
            rule_type="retrieval_gate",
            conditions={"metadata_key_equals": {"key": "blocked", "value": True}},
            action="deny",
        )
    )

    decision = engine.evaluate(
        MemoryGovernanceEvaluationRequest(
            memory=memory("memory-1", metadata={"blocked": True}),
            action_type="memory.retrieve",
            owner_scope=["workspace:main"],
        )
    )

    assert decision.decision == "deny"
    assert decision.rule_ids == ["rule-deny"]


def test_memory_service_blocks_governance_denied_write() -> None:
    """MemoryService applies governance after policy authorization."""
    engine, _repository = make_engine()
    engine.create_rule(
        rule(
            governance_rule_id="rule-write-deny",
            rule_type="write_gate",
            conditions={"metadata_key_equals": {"key": "blocked", "value": True}},
            action="deny",
        )
    )
    service = PostgresMemoryService(
        InMemorySemanticMemoryAdapter(),
        AllowPolicy(),
        governance_engine=engine,
    )

    with pytest.raises(MemoryGovernanceDenied):
        service.create(memory("memory-1", metadata={"blocked": True}))


def test_decay_score_reduces_old_low_confidence_memory() -> None:
    """Decay score is deterministic and bounded."""
    service = make_decay_service(memory_service=object())
    record = memory(
        "memory-1",
        confidence=0.3,
        created_at=datetime.now(UTC) - timedelta(days=180),
    )

    score, factors = service.compute_decay_score(record)

    assert 0 <= score < record.confidence
    assert factors["age_days"] >= 179
    assert "low_confidence_penalty" in factors


def test_retention_sweep_expires_matching_memory() -> None:
    """Retention service marks stale working memory expired without hard delete."""
    engine, repository = make_engine()
    engine.create_rule(
        rule(
            governance_rule_id="rule-expire",
            rule_type="retention",
            memory_types=["working"],
            conditions={"stale_after_days": 1},
            action="expire",
        )
    )
    memory_service = PostgresMemoryService(
        InMemorySemanticMemoryAdapter(),
        AllowPolicy(),
        governance_engine=engine,
    )
    memory_service.create(
        memory(
            "memory-1",
            memory_type="working",
            created_at=datetime.now(UTC) - timedelta(days=3),
        )
    )
    retention = MemoryRetentionService(
        memory_service=memory_service,
        governance_engine=engine,
        decay_service=make_decay_service(memory_service=memory_service, repository=repository),
        policy_adapter=AllowPolicy(),
        telemetry_service=None,
    )

    result = retention.sweep(
        MemoryRetentionSweepRequest(
            owner_scope=["workspace:main"],
            dry_run=False,
            limit=10,
        )
    )

    assert result.expired == 1
    assert memory_service.get("memory-1") is None


def test_forgetting_requires_approval_by_default() -> None:
    """Forget request creates a pending approval before destructive action."""
    memory_service, semantic_adapter = make_memory_service()
    memory_service.create(memory("memory-1", content_ref="content://source"))
    service = make_forgetting_service(memory_service, semantic_adapter)

    result = service.forget(
        ForgetMemoryRequest(
            target_type="memory",
            target_id="memory-1",
            owner_scope=["workspace:main"],
            reason="remove stale recall",
        )
    )

    assert result.status == "pending_approval"
    assert result.forgotten is False
    assert result.preserved_refs == ["content://source"]
    assert memory_service.get("memory-1") is not None


def test_forgetting_with_approval_soft_deletes_memory_and_semantic_index() -> None:
    """Approved forget soft-deletes canonical memory and semantic recall."""
    memory_service, semantic_adapter = make_memory_service()
    memory_service.create(memory("memory-1"))
    service = make_forgetting_service(memory_service, semantic_adapter)

    result = service.forget(
        ForgetMemoryRequest(
            target_type="memory",
            target_id="memory-1",
            owner_scope=["workspace:main"],
            reason="approved cleanup",
            approval_present=True,
        )
    )

    assert result.status == "completed"
    assert result.forgotten is True
    assert memory_service.get("memory-1") is None
    assert semantic_adapter.get("memory-1") is None


def test_conflict_scan_detects_duplicates_and_resolves() -> None:
    """Conflict service detects duplicate summaries and resolves records."""
    memory_service, _adapter = make_memory_service()
    memory_service.create(memory("memory-1", summary="alpha beta"))
    memory_service.create(memory("memory-2", summary="Alpha beta"))
    service = MemoryConflictService(
        memory_service=memory_service,
        governance_repository=MemoryGovernanceRepository(
            database_url="sqlite+pysqlite:///:memory:"
        ),
        policy_adapter=AllowPolicy(),
        telemetry_service=None,
        settings=make_test_settings(),
    )

    conflicts = service.scan(
        MemoryConflictScanRequest(owner_scope=["workspace:main"], conflict_types=["duplicate"])
    )
    resolved = service.resolve(
        MemoryConflictResolutionRequest(
            conflict_id=conflicts[0].conflict_id,
            resolution="keep_highest_confidence",
            reason="deterministic resolution",
        )
    )

    assert conflicts[0].conflict_type == "duplicate"
    assert resolved.status == "resolved"


def test_compaction_dry_run_creates_deterministic_output_ids_without_saving() -> None:
    """Dry-run compaction returns a plan without storing output memory."""
    memory_service, _adapter = make_memory_service()
    memory_service.create(memory("memory-1", summary="alpha beta"))
    memory_service.create(memory("memory-2", summary="alpha gamma"))
    service = make_compaction_service(memory_service)

    result = service.compact(
        MemoryCompactionRequest(
            owner_scope=["workspace:main"],
            strategy="deterministic_extract",
            dry_run=True,
        )
    )

    assert result.status == "completed"
    assert result.compacted_count == 1
    assert memory_service.get(result.output_memory_ids[0]) is None


def test_retrieval_router_filters_governance_expired_memory() -> None:
    """RetrievalRouter filters governed recall candidates."""
    memory_service = FakeMemoryService(
        [memory("memory-1", metadata={"governance_status": "expired"})]
    )
    router = RetrievalRouter(policy_adapter=AllowPolicy(), memory_service=memory_service)

    result = router.retrieve(make_retrieval_request())

    assert result.items == []
    assert "memory_governance_filtered_count:1" in result.constraints


def test_memory_governance_api_works_with_fakes() -> None:
    """Governance API routes expose public contracts only."""
    engine, _repository = make_engine()
    memory_service, semantic_adapter = make_memory_service()
    memory_service.create(memory("memory-1"))
    conflict_service = MemoryConflictService(
        memory_service=memory_service,
        governance_repository=MemoryGovernanceRepository(
            database_url="sqlite+pysqlite:///:memory:"
        ),
        policy_adapter=AllowPolicy(),
        telemetry_service=None,
        settings=make_test_settings(),
    )
    compaction_service = make_compaction_service(memory_service)
    with governance_overrides(
        engine=engine,
        decay=make_decay_service(memory_service=memory_service),
        retention=MemoryRetentionService(
            memory_service=memory_service,
            governance_engine=engine,
            decay_service=make_decay_service(memory_service=memory_service),
            policy_adapter=AllowPolicy(),
            telemetry_service=None,
        ),
        forgetting=make_forgetting_service(memory_service, semantic_adapter),
        conflicts=conflict_service,
        compaction=compaction_service,
    ):
        client = TestClient(app)
        created = client.post("/brain/memory/governance/rules", json=rule().model_dump(mode="json"))
        listed = client.get("/brain/memory/governance/rules")
        evaluated = client.post(
            "/brain/memory/governance/evaluate",
            json={
                "memory": memory("memory-api").model_dump(mode="json"),
                "action_type": "memory.retrieve",
                "owner_scope": ["workspace:main"],
            },
        )
        decayed = client.post(
            "/brain/memory/decay/recompute",
            json={"scope": ["workspace:main"], "dry_run": True},
        )
        forgotten = client.post(
            "/brain/memory/forget",
            json={
                "target_type": "memory",
                "target_id": "memory-1",
                "owner_scope": ["workspace:main"],
                "reason": "api request",
            },
        )
        conflicts = client.post(
            "/brain/memory/conflicts",
            json={"owner_scope": ["workspace:main"], "conflict_types": ["duplicate"]},
        )
        compacted = client.post(
            "/brain/memory/compact",
            json={"owner_scope": ["workspace:main"], "dry_run": True},
        )

    assert created.status_code == 200
    assert listed.status_code == 200
    assert evaluated.json()["decision"] == "allow"
    assert decayed.status_code == 200
    assert forgotten.json()["status"] == "pending_approval"
    assert conflicts.status_code == 200
    assert compacted.json()["status"] == "completed"


class AllowPolicy:
    """Allow-all policy fake."""

    def __init__(self, *, deny_actions: set[str] | None = None) -> None:
        self.deny_actions = deny_actions or set()
        self.requests: list[PolicyRequest] = []

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        self.requests.append(request)
        allow = request.action_type not in self.deny_actions
        return PolicyDecision(
            decision_id=f"decision-{len(self.requests)}",
            trace_id=request.trace_id or "",
            allow=allow,
            approval_required=False,
            reason="allowed" if allow else "denied",
            constraints=[] if allow else ["blocked"],
            audit_level="standard",
        )


class FakeApprovalService:
    """Approval fake."""

    def create_request(self, request: ApprovalCreateRequest) -> object:
        return approval_request()


class FakeMemoryService:
    """Retrieval memory fake."""

    def __init__(self, records: list[MemoryRecord]) -> None:
        self.records = records

    def retrieve(self, request: MemoryRetrievalRequest) -> list[MemoryRecord]:
        return self.records


def make_engine() -> tuple[MemoryGovernanceEngine, MemoryGovernanceRepository]:
    """Create governance engine with SQLite repository."""
    repository = MemoryGovernanceRepository(database_url="sqlite+pysqlite:///:memory:")
    engine = MemoryGovernanceEngine(
        governance_repository=repository,
        risk_engine=None,
        approval_service=None,
        policy_adapter=AllowPolicy(),
        telemetry_service=None,
        settings=make_test_settings(),
    )
    return engine, repository


def make_memory_service() -> tuple[PostgresMemoryService, InMemorySemanticMemoryAdapter]:
    """Create canonical memory service with in-memory adapter."""
    adapter = InMemorySemanticMemoryAdapter()
    service = PostgresMemoryService(adapter, AllowPolicy())
    return service, adapter


def make_decay_service(
    *,
    memory_service: object,
    repository: MemoryGovernanceRepository | None = None,
) -> MemoryDecayService:
    """Create decay service."""
    return MemoryDecayService(
        governance_repository=repository
        or MemoryGovernanceRepository(database_url="sqlite+pysqlite:///:memory:"),
        memory_service=memory_service,
        telemetry_service=None,
        settings=make_test_settings(),
    )


def make_forgetting_service(
    memory_service: PostgresMemoryService,
    semantic_adapter: InMemorySemanticMemoryAdapter,
) -> MemoryForgettingService:
    """Create forgetting service."""
    semantic_service = type(
        "SemanticService",
        (),
        {"forget": lambda self, memory_id, scope: semantic_adapter.forget(memory_id)},
    )()
    return MemoryForgettingService(
        memory_service=memory_service,
        semantic_memory_service=semantic_service,
        graph_memory_service=None,
        evidence_service=None,
        skill_service=None,
        trace_repository=None,
        risk_engine=None,
        approval_service=FakeApprovalService(),
        policy_adapter=AllowPolicy(),
        governance_repository=MemoryGovernanceRepository(
            database_url="sqlite+pysqlite:///:memory:"
        ),
        telemetry_service=None,
        settings=make_test_settings(),
    )


def make_compaction_service(memory_service: PostgresMemoryService) -> MemoryCompactionService:
    """Create compaction service."""
    return MemoryCompactionService(
        memory_service=memory_service,
        governance_repository=MemoryGovernanceRepository(
            database_url="sqlite+pysqlite:///:memory:"
        ),
        policy_adapter=AllowPolicy(),
        approval_service=FakeApprovalService(),
        telemetry_service=None,
        settings=make_test_settings(),
    )


def memory(
    memory_id: str,
    *,
    summary: str = "alpha beta",
    memory_type: Any = "semantic",
    metadata: dict[str, Any] | None = None,
    confidence: float = 0.8,
    created_at: datetime | None = None,
    content_ref: str | None = None,
) -> MemoryRecord:
    """Create a memory record."""
    return MemoryRecord(
        memory_id=memory_id,
        memory_type=memory_type,
        owner_scope=["workspace:main"],
        source_event_id=None,
        content_ref=content_ref,
        summary=summary,
        confidence=confidence,
        sensitivity="internal",
        created_at=created_at or datetime.now(UTC),
        expires_at=None,
        metadata=metadata or {},
    )


def rule(
    *,
    governance_rule_id: str = "rule-1",
    name: str = "Generic rule",
    rule_type: Any = "retrieval_gate",
    memory_types: list[Any] | None = None,
    conditions: dict[str, Any] | None = None,
    action: Any = "allow",
    metadata: dict[str, Any] | None = None,
) -> MemoryGovernanceRule:
    """Create a governance rule."""
    return MemoryGovernanceRule(
        governance_rule_id=governance_rule_id,
        name=name,
        description="Generic memory governance rule.",
        status="active",
        rule_type=rule_type,
        memory_types=memory_types or [],
        owner_scope=["workspace:main"],
        sensitivity_levels=[],
        conditions=conditions or {},
        action=action,
        priority=0,
        metadata=metadata or {},
        created_by="tester",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def make_retrieval_request() -> object:
    """Create retrieval request without importing test-only helper."""
    from aion_brain.contracts.retrieval import RetrievalRequest

    return RetrievalRequest(
        retrieval_id="retrieval-1",
        trace_id="trace-1",
        intent_id="intent-1",
        query="alpha",
        scope=["workspace:main"],
        requested_sources=["lexical_memory"],
        limit=10,
    )


def make_test_settings() -> Settings:
    """Return settings with governance toggles enabled."""
    return Settings(
        database_url="sqlite+pysqlite:///:memory:",
        opa_url="http://opa.test",
        memory_forgetting_requires_approval=True,
        memory_compaction_requires_approval=False,
    )


def governance_overrides(
    *,
    engine: MemoryGovernanceEngine,
    decay: MemoryDecayService,
    retention: MemoryRetentionService,
    forgetting: MemoryForgettingService,
    conflicts: MemoryConflictService,
    compaction: MemoryCompactionService,
) -> object:
    """Install dependency overrides for governance API tests."""

    class OverrideContext:
        def __enter__(self) -> None:
            app.dependency_overrides[get_memory_governance_engine] = lambda: engine
            app.dependency_overrides[get_memory_decay_service] = lambda: decay
            app.dependency_overrides[get_memory_retention_service] = lambda: retention
            app.dependency_overrides[get_memory_forgetting_service] = lambda: forgetting
            app.dependency_overrides[get_memory_conflict_service] = lambda: conflicts
            app.dependency_overrides[get_memory_compaction_service] = lambda: compaction
            app.dependency_overrides[get_actor_context] = lambda: ActorContext(
                actor_id="actor-1",
                workspace_id="workspace-1",
                roles=["owner"],
                permissions=["memory.retrieve"],
                security_scope=["workspace:main"],
                dev_mode=True,
            )

        def __exit__(self, *args: object) -> None:
            app.dependency_overrides.clear()

    return OverrideContext()
