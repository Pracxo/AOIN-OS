"""Shared helpers for Contract Registry tests."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.pool import StaticPool

from aion_brain.contract_registry.hash import hash_schema
from aion_brain.contract_registry.repository import ContractRegistryRepository
from aion_brain.contracts.compatibility import (
    CompatibilityRule,
    InterfaceDriftFinding,
)
from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractSnapshot,
    InterfaceInventoryRecord,
)
from aion_brain.contracts.policy import PolicyDecision, PolicyRequest

SCOPE = ["workspace:main"]


class AllowPolicy:
    """Always-allow policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=True,
            approval_required=False,
            reason="allowed",
            constraints=[],
            audit_level="standard",
        )


class DenyPolicy:
    """Always-deny policy fake."""

    def authorize(self, request: PolicyRequest) -> PolicyDecision:
        return PolicyDecision(
            decision_id=f"decision-{request.request_id}",
            trace_id=request.trace_id or "",
            allow=False,
            approval_required=False,
            reason="denied",
            constraints=[],
            audit_level="standard",
        )


class FakeTelemetry:
    """Collect emitted telemetry records."""

    def __init__(self) -> None:
        self.events: list[object] = []

    def emit(self, event: object) -> None:
        self.events.append(event)


def repository() -> ContractRegistryRepository:
    """Return an in-memory Contract Registry repository."""
    engine = create_engine(
        "sqlite+pysqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return ContractRegistryRepository(engine=engine)


def schema(
    *, required: list[str] | None = None, extra: dict[str, Any] | None = None
) -> dict[str, Any]:
    """Return a small JSON-schema-like payload."""
    value: dict[str, Any] = {
        "type": "object",
        "properties": {"name": {"type": "string"}},
        "required": required or [],
    }
    if extra:
        value.update(extra)
    return value


def contract_record(
    key: str = "aion.contract.Test",
    *,
    schema_payload: dict[str, Any] | None = None,
    status: str = "active",
) -> ContractIndexRecord:
    """Return a valid contract index record."""
    payload = schema_payload or schema()
    return ContractIndexRecord(
        contract_index_id=f"contract-{key.replace('.', '-')}",
        contract_key=key,
        contract_type="pydantic_model",
        source_path="services/brain-api/src/aion_brain/contracts/test.py",
        source_symbol=key.rsplit(".", 1)[-1],
        status=status,  # type: ignore[arg-type]
        visibility="public",
        version="0.1.0",
        schema_hash=hash_schema(payload),
        schema=payload,
        owner_scope=SCOPE,
        tags=["test"],
        metadata={"source_mutated": False},
    )


def interface_record(
    key: str = "GET /brain/example",
    *,
    interface_type: str = "api_route",
    path: str | None = "/brain/example",
    method: str | None = "GET",
    descriptor: dict[str, Any] | None = None,
    source_system: str = "fastapi",
    visibility: str = "public",
) -> InterfaceInventoryRecord:
    """Return a valid interface inventory record."""
    payload = descriptor or {"path": path, "method": method}
    return InterfaceInventoryRecord(
        interface_id=f"interface-{abs(hash((key, interface_type))) % 1000000}",
        interface_key=key,
        interface_type=interface_type,  # type: ignore[arg-type]
        source_system=source_system,
        status="active",
        visibility=visibility,  # type: ignore[arg-type]
        version="0.1.0",
        path=path,
        method=method,
        command=payload.get("command") if isinstance(payload.get("command"), str) else None,
        action=payload.get("action") if isinstance(payload.get("action"), str) else None,
        schema_hash=hash_schema(payload),
        descriptor=payload,
        owner_scope=SCOPE,
        metadata={"source_mutated": False},
    )


def snapshot(
    snapshot_id: str,
    *,
    contracts: list[ContractIndexRecord] | None = None,
    interfaces: list[InterfaceInventoryRecord] | None = None,
) -> ContractSnapshot:
    """Return a contract snapshot with a deterministic manifest."""
    contract_items = contracts or []
    interface_items = interfaces or []
    manifest = {
        "contracts": [item.model_dump(mode="json") for item in contract_items],
        "interfaces": [item.model_dump(mode="json") for item in interface_items],
    }
    return ContractSnapshot(
        contract_snapshot_id=snapshot_id,
        trace_id="trace-1",
        snapshot_type="manual",
        status="created",
        version="0.1.0",
        owner_scope=SCOPE,
        contract_count=len(contract_items),
        interface_count=len(interface_items),
        policy_action_count=sum(
            1 for item in interface_items if item.interface_type == "policy_action"
        ),
        route_count=sum(1 for item in interface_items if item.interface_type == "api_route"),
        sdk_resource_count=sum(
            1 for item in interface_items if item.interface_type == "sdk_resource"
        ),
        cli_command_count=sum(
            1 for item in interface_items if item.interface_type == "cli_command"
        ),
        setting_count=sum(1 for item in interface_items if item.interface_type == "env_setting"),
        telemetry_count=sum(
            1
            for item in interface_items
            if item.interface_type in {"telemetry_event", "telemetry_node"}
        ),
        root_hash=hash_schema(manifest),
        manifest=manifest,
        report={"source_mutated": False},
        metadata={"source_mutated": False},
        created_by="tester",
        created_at=datetime.now(UTC),
    )


def compatibility_rule(rule_type: str = "no_removed_route") -> CompatibilityRule:
    """Return a valid compatibility rule."""
    return CompatibilityRule(
        compatibility_rule_id=f"rule-{rule_type}",
        name=rule_type,
        description="Generic compatibility rule.",
        status="active",
        rule_type=rule_type,  # type: ignore[arg-type]
        severity="high",
        applies_to=["interface"],
        rule={"rule_type": rule_type},
        owner_scope=SCOPE,
        metadata={},
        created_by="tester",
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )


def drift_finding(
    finding_id: str = "finding-1",
    *,
    finding_type: str = "removed_route",
    breaking: bool = True,
    severity: str = "high",
) -> InterfaceDriftFinding:
    """Return an interface drift finding."""
    return InterfaceDriftFinding(
        drift_finding_id=finding_id,
        trace_id="trace-1",
        compatibility_scan_id="scan-1",
        finding_type=finding_type,  # type: ignore[arg-type]
        interface_type="api_route",
        contract_key=None,
        interface_key="GET /brain/example",
        source_system="fastapi",
        severity=severity,  # type: ignore[arg-type]
        status="open",
        breaking=breaking,
        title="Removed route",
        description="A route was removed.",
        old_ref="snapshot-old",
        new_ref="snapshot-new",
        recommended_action="Review the route.",
        metadata={"source_mutated": False},
        created_at=datetime.now(UTC),
    )


class FakeSnapshotService:
    """Snapshot service fake used by compatibility scanner tests."""

    def __init__(self, baseline: ContractSnapshot, candidate: ContractSnapshot) -> None:
        self.baseline = baseline
        self.candidate = candidate

    def get_snapshot(self, snapshot_id: str, scope: list[str]) -> ContractSnapshot | None:
        if snapshot_id == self.baseline.contract_snapshot_id:
            return self.baseline
        if snapshot_id == self.candidate.contract_snapshot_id:
            return self.candidate
        return None

    def create_snapshot(self, scope: list[str], snapshot_type: str = "manual") -> ContractSnapshot:
        return self.baseline if snapshot_type == "baseline" else self.candidate


class FakeRuleService:
    """Rule service fake used by compatibility scanner tests."""

    def list_rules(
        self,
        scope: list[str],
        status: str | None = None,
        limit: int = 100,
    ) -> list[CompatibilityRule]:
        return [compatibility_rule()]
