"""Persistent repository for AION Contract Registry records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.compatibility import (
    CompatibilityRule,
    CompatibilityScan,
    InterfaceDriftFinding,
)
from aion_brain.contracts.contract_registry import (
    ContractIndexRecord,
    ContractRegistryReport,
    ContractSnapshot,
    InterfaceInventoryRecord,
    MigrationNote,
)

contract_registry_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")


aion_contract_index_records = Table(
    "aion_contract_index_records",
    contract_registry_metadata,
    Column("contract_index_id", Text, primary_key=True),
    Column("contract_key", Text, nullable=False),
    Column("contract_type", Text, nullable=False),
    Column("source_path", Text, nullable=False),
    Column("source_symbol", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("visibility", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("schema_hash", Text, nullable=False),
    Column("schema", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("tags", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
    Column("last_seen_at", DateTime(timezone=True), nullable=False),
    Column("deprecated_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_contract_index_contract_key", "contract_key"),
    Index("ix_aion_contract_index_contract_type", "contract_type"),
    Index("ix_aion_contract_index_source_path", "source_path"),
    Index("ix_aion_contract_index_source_symbol", "source_symbol"),
    Index("ix_aion_contract_index_status", "status"),
    Index("ix_aion_contract_index_visibility", "visibility"),
    Index("ix_aion_contract_index_version", "version"),
    Index("ix_aion_contract_index_schema_hash", "schema_hash"),
    Index("ix_aion_contract_index_first_seen_at", "first_seen_at"),
    Index("ix_aion_contract_index_last_seen_at", "last_seen_at"),
    Index("ix_aion_contract_index_deleted_at", "deleted_at"),
)

aion_interface_inventory_records = Table(
    "aion_interface_inventory_records",
    contract_registry_metadata,
    Column("interface_id", Text, primary_key=True),
    Column("interface_key", Text, nullable=False),
    Column("interface_type", Text, nullable=False),
    Column("source_system", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("visibility", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("path", Text, nullable=True),
    Column("method", Text, nullable=True),
    Column("command", Text, nullable=True),
    Column("action", Text, nullable=True),
    Column("setting_key", Text, nullable=True),
    Column("feature_key", Text, nullable=True),
    Column("telemetry_key", Text, nullable=True),
    Column("resource_type", Text, nullable=True),
    Column("schema_hash", Text, nullable=False),
    Column("descriptor", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("first_seen_at", DateTime(timezone=True), nullable=False),
    Column("last_seen_at", DateTime(timezone=True), nullable=False),
    Column("deprecated_at", DateTime(timezone=True), nullable=True),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_interface_inventory_interface_key", "interface_key"),
    Index("ix_aion_interface_inventory_interface_type", "interface_type"),
    Index("ix_aion_interface_inventory_source_system", "source_system"),
    Index("ix_aion_interface_inventory_status", "status"),
    Index("ix_aion_interface_inventory_visibility", "visibility"),
    Index("ix_aion_interface_inventory_version", "version"),
    Index("ix_aion_interface_inventory_path", "path"),
    Index("ix_aion_interface_inventory_method", "method"),
    Index("ix_aion_interface_inventory_command", "command"),
    Index("ix_aion_interface_inventory_action", "action"),
    Index("ix_aion_interface_inventory_setting_key", "setting_key"),
    Index("ix_aion_interface_inventory_feature_key", "feature_key"),
    Index("ix_aion_interface_inventory_telemetry_key", "telemetry_key"),
    Index("ix_aion_interface_inventory_resource_type", "resource_type"),
    Index("ix_aion_interface_inventory_schema_hash", "schema_hash"),
    Index("ix_aion_interface_inventory_deleted_at", "deleted_at"),
)

aion_contract_snapshots = Table(
    "aion_contract_snapshots",
    contract_registry_metadata,
    Column("contract_snapshot_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("snapshot_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("contract_count", Integer, nullable=False),
    Column("interface_count", Integer, nullable=False),
    Column("policy_action_count", Integer, nullable=False),
    Column("route_count", Integer, nullable=False),
    Column("sdk_resource_count", Integer, nullable=False),
    Column("cli_command_count", Integer, nullable=False),
    Column("setting_count", Integer, nullable=False),
    Column("telemetry_count", Integer, nullable=False),
    Column("root_hash", Text, nullable=False),
    Column("manifest", json_payload_type, nullable=False),
    Column("report", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_contract_snapshots_trace", "trace_id"),
    Index("ix_aion_contract_snapshots_snapshot_type", "snapshot_type"),
    Index("ix_aion_contract_snapshots_status", "status"),
    Index("ix_aion_contract_snapshots_version", "version"),
    Index("ix_aion_contract_snapshots_root_hash", "root_hash"),
    Index("ix_aion_contract_snapshots_created_at", "created_at"),
)

aion_compatibility_rules = Table(
    "aion_compatibility_rules",
    contract_registry_metadata,
    Column("compatibility_rule_id", Text, primary_key=True),
    Column("name", Text, nullable=False, unique=True),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("rule_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("applies_to", json_payload_type, nullable=False),
    Column("rule", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_compat_rules_name", "name"),
    Index("ix_aion_compat_rules_status", "status"),
    Index("ix_aion_compat_rules_rule_type", "rule_type"),
    Index("ix_aion_compat_rules_severity", "severity"),
    Index("ix_aion_compat_rules_created_at", "created_at"),
)

aion_interface_drift_findings = Table(
    "aion_interface_drift_findings",
    contract_registry_metadata,
    Column("drift_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("compatibility_scan_id", Text, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("interface_type", Text, nullable=False),
    Column("contract_key", Text, nullable=True),
    Column("interface_key", Text, nullable=True),
    Column("source_system", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("breaking", Boolean, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("old_ref", Text, nullable=True),
    Column("new_ref", Text, nullable=True),
    Column("recommended_action", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Column("dismissed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_drift_findings_trace", "trace_id"),
    Index("ix_aion_drift_findings_scan", "compatibility_scan_id"),
    Index("ix_aion_drift_findings_finding_type", "finding_type"),
    Index("ix_aion_drift_findings_interface_type", "interface_type"),
    Index("ix_aion_drift_findings_contract_key", "contract_key"),
    Index("ix_aion_drift_findings_interface_key", "interface_key"),
    Index("ix_aion_drift_findings_source_system", "source_system"),
    Index("ix_aion_drift_findings_severity", "severity"),
    Index("ix_aion_drift_findings_status", "status"),
    Index("ix_aion_drift_findings_breaking", "breaking"),
    Index("ix_aion_drift_findings_created_at", "created_at"),
)

aion_compatibility_scans = Table(
    "aion_compatibility_scans",
    contract_registry_metadata,
    Column("compatibility_scan_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("mode", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("baseline_snapshot_id", Text, nullable=True),
    Column("candidate_snapshot_id", Text, nullable=True),
    Column("scan_scope", json_payload_type, nullable=False),
    Column("rules_applied", json_payload_type, nullable=False),
    Column("findings_count", Integer, nullable=False),
    Column("breaking_count", Integer, nullable=False),
    Column("warning_count", Integer, nullable=False),
    Column("passed_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("result", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("completed_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_compat_scans_trace", "trace_id"),
    Index("ix_aion_compat_scans_actor", "actor_id"),
    Index("ix_aion_compat_scans_workspace", "workspace_id"),
    Index("ix_aion_compat_scans_status", "status"),
    Index("ix_aion_compat_scans_mode", "mode"),
    Index("ix_aion_compat_scans_baseline", "baseline_snapshot_id"),
    Index("ix_aion_compat_scans_candidate", "candidate_snapshot_id"),
    Index("ix_aion_compat_scans_findings", "findings_count"),
    Index("ix_aion_compat_scans_breaking", "breaking_count"),
    Index("ix_aion_compat_scans_warning", "warning_count"),
    Index("ix_aion_compat_scans_created_at", "created_at"),
)

aion_migration_notes = Table(
    "aion_migration_notes",
    contract_registry_metadata,
    Column("migration_note_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("compatibility_scan_id", Text, nullable=True),
    Column("finding_id", Text, nullable=True),
    Column("note_type", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("title", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("affected_contracts", json_payload_type, nullable=False),
    Column("affected_interfaces", json_payload_type, nullable=False),
    Column("migration_steps", json_payload_type, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("archived_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_migration_notes_trace", "trace_id"),
    Index("ix_aion_migration_notes_scan", "compatibility_scan_id"),
    Index("ix_aion_migration_notes_finding", "finding_id"),
    Index("ix_aion_migration_notes_note_type", "note_type"),
    Index("ix_aion_migration_notes_status", "status"),
    Index("ix_aion_migration_notes_created_at", "created_at"),
)

aion_contract_registry_reports = Table(
    "aion_contract_registry_reports",
    contract_registry_metadata,
    Column("contract_report_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("snapshot_id", Text, nullable=True),
    Column("latest_scan_id", Text, nullable=True),
    Column("contract_count", Integer, nullable=False),
    Column("interface_count", Integer, nullable=False),
    Column("active_breaking_findings", Integer, nullable=False),
    Column("active_warning_findings", Integer, nullable=False),
    Column("deprecated_count", Integer, nullable=False),
    Column("missing_sdk_count", Integer, nullable=False),
    Column("missing_cli_count", Integer, nullable=False),
    Column("missing_policy_count", Integer, nullable=False),
    Column("findings", json_payload_type, nullable=False),
    Column("recommendations", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_contract_reports_trace", "trace_id"),
    Index("ix_aion_contract_reports_status", "status"),
    Index("ix_aion_contract_reports_snapshot", "snapshot_id"),
    Index("ix_aion_contract_reports_latest_scan", "latest_scan_id"),
    Index("ix_aion_contract_reports_breaking", "active_breaking_findings"),
    Index("ix_aion_contract_reports_warning", "active_warning_findings"),
    Index("ix_aion_contract_reports_created_at", "created_at"),
)


class ContractRegistryRepository:
    """Store contract registry records without owning source code contracts."""

    def __init__(
        self,
        database_url: str | None = None,
        *,
        engine: Engine | None = None,
        auto_create: bool = True,
    ) -> None:
        if engine is None:
            if database_url is None:
                raise ValueError("database_url or engine is required")
            if database_url.startswith("sqlite"):
                self._engine = create_engine(
                    database_url,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool,
                )
            else:
                self._engine = create_engine(database_url, poolclass=QueuePool, pool_pre_ping=True)
        else:
            self._engine = engine
        self._auto_create = auto_create
        self._schema_ready = False

    def save_contract(self, record: ContractIndexRecord) -> ContractIndexRecord:
        now = datetime.now(UTC)
        stored = record.model_copy(
            update={
                "first_seen_at": record.first_seen_at or now,
                "last_seen_at": now,
            }
        )
        self._replace(
            aion_contract_index_records,
            "contract_index_id",
            stored.contract_index_id,
            _model_values(aion_contract_index_records, stored),
        )
        return stored

    def list_contracts(
        self,
        *,
        contract_type: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ContractIndexRecord]:
        return self._list(
            aion_contract_index_records,
            ContractIndexRecord,
            {"contract_type": contract_type, "status": status},
            "last_seen_at",
            limit,
        )

    def save_interface(self, record: InterfaceInventoryRecord) -> InterfaceInventoryRecord:
        now = datetime.now(UTC)
        stored = record.model_copy(
            update={
                "first_seen_at": record.first_seen_at or now,
                "last_seen_at": now,
            }
        )
        self._replace(
            aion_interface_inventory_records,
            "interface_id",
            stored.interface_id,
            _model_values(aion_interface_inventory_records, stored),
        )
        return stored

    def list_interfaces(
        self,
        *,
        interface_type: str | None = None,
        source_system: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[InterfaceInventoryRecord]:
        return self._list(
            aion_interface_inventory_records,
            InterfaceInventoryRecord,
            {
                "interface_type": interface_type,
                "source_system": source_system,
                "status": status,
            },
            "last_seen_at",
            limit,
        )

    def save_snapshot(self, snapshot: ContractSnapshot) -> ContractSnapshot:
        stored = snapshot.model_copy(
            update={"created_at": snapshot.created_at or datetime.now(UTC)}
        )
        self._replace(
            aion_contract_snapshots,
            "contract_snapshot_id",
            stored.contract_snapshot_id,
            _model_values(aion_contract_snapshots, stored),
        )
        return stored

    def get_snapshot(self, contract_snapshot_id: str) -> ContractSnapshot | None:
        return self._get(
            aion_contract_snapshots,
            "contract_snapshot_id",
            contract_snapshot_id,
            ContractSnapshot,
        )

    def latest_snapshot(self) -> ContractSnapshot | None:
        rows = self.list_snapshots(limit=1)
        return rows[0] if rows else None

    def list_snapshots(
        self,
        *,
        snapshot_type: str | None = None,
        status: str | None = None,
        limit: int = 50,
    ) -> list[ContractSnapshot]:
        return self._list(
            aion_contract_snapshots,
            ContractSnapshot,
            {"snapshot_type": snapshot_type, "status": status},
            "created_at",
            limit,
        )

    def save_rule(self, rule: CompatibilityRule) -> CompatibilityRule:
        now = datetime.now(UTC)
        stored = rule.model_copy(
            update={
                "created_at": rule.created_at or now,
                "updated_at": now,
            }
        )
        self._replace(
            aion_compatibility_rules,
            "compatibility_rule_id",
            stored.compatibility_rule_id,
            _model_values(aion_compatibility_rules, stored),
        )
        return stored

    def get_rule(self, compatibility_rule_id: str) -> CompatibilityRule | None:
        return self._get(
            aion_compatibility_rules,
            "compatibility_rule_id",
            compatibility_rule_id,
            CompatibilityRule,
        )

    def list_rules(
        self,
        *,
        status: str | None = None,
        rule_type: str | None = None,
        limit: int = 100,
    ) -> list[CompatibilityRule]:
        return self._list(
            aion_compatibility_rules,
            CompatibilityRule,
            {"status": status, "rule_type": rule_type},
            "created_at",
            limit,
        )

    def save_finding(self, finding: InterfaceDriftFinding) -> InterfaceDriftFinding:
        stored = finding.model_copy(update={"created_at": finding.created_at or datetime.now(UTC)})
        self._replace(
            aion_interface_drift_findings,
            "drift_finding_id",
            stored.drift_finding_id,
            _model_values(aion_interface_drift_findings, stored),
        )
        return stored

    def get_finding(self, drift_finding_id: str) -> InterfaceDriftFinding | None:
        return self._get(
            aion_interface_drift_findings,
            "drift_finding_id",
            drift_finding_id,
            InterfaceDriftFinding,
        )

    def list_findings(
        self,
        *,
        status: str | None = None,
        severity: str | None = None,
        breaking: bool | None = None,
        interface_type: str | None = None,
        limit: int = 100,
    ) -> list[InterfaceDriftFinding]:
        return self._list(
            aion_interface_drift_findings,
            InterfaceDriftFinding,
            {
                "status": status,
                "severity": severity,
                "breaking": breaking,
                "interface_type": interface_type,
            },
            "created_at",
            limit,
        )

    def save_scan(self, scan: CompatibilityScan) -> CompatibilityScan:
        now = datetime.now(UTC)
        stored = scan.model_copy(
            update={
                "created_at": scan.created_at or now,
                "completed_at": scan.completed_at or now,
            }
        )
        self._replace(
            aion_compatibility_scans,
            "compatibility_scan_id",
            stored.compatibility_scan_id,
            _model_values(aion_compatibility_scans, stored),
        )
        return stored

    def get_scan(self, compatibility_scan_id: str) -> CompatibilityScan | None:
        return self._get(
            aion_compatibility_scans,
            "compatibility_scan_id",
            compatibility_scan_id,
            CompatibilityScan,
        )

    def latest_scan(self) -> CompatibilityScan | None:
        rows = self._list(
            aion_compatibility_scans,
            CompatibilityScan,
            {},
            "created_at",
            1,
        )
        return rows[0] if rows else None

    def list_scans(
        self,
        *,
        status: str | None = None,
        mode: str | None = None,
        limit: int = 100,
    ) -> list[CompatibilityScan]:
        return self._list(
            aion_compatibility_scans,
            CompatibilityScan,
            {"status": status, "mode": mode},
            "created_at",
            limit,
        )

    def save_migration_note(self, note: MigrationNote) -> MigrationNote:
        stored = note.model_copy(update={"created_at": note.created_at or datetime.now(UTC)})
        self._replace(
            aion_migration_notes,
            "migration_note_id",
            stored.migration_note_id,
            _model_values(aion_migration_notes, stored),
        )
        return stored

    def get_migration_note(self, migration_note_id: str) -> MigrationNote | None:
        return self._get(
            aion_migration_notes, "migration_note_id", migration_note_id, MigrationNote
        )

    def list_migration_notes(
        self,
        *,
        status: str | None = None,
        note_type: str | None = None,
        limit: int = 100,
    ) -> list[MigrationNote]:
        return self._list(
            aion_migration_notes,
            MigrationNote,
            {"status": status, "note_type": note_type},
            "created_at",
            limit,
        )

    def save_report(self, report: ContractRegistryReport) -> ContractRegistryReport:
        stored = report.model_copy(update={"created_at": report.created_at or datetime.now(UTC)})
        self._replace(
            aion_contract_registry_reports,
            "contract_report_id",
            stored.contract_report_id,
            _model_values(aion_contract_registry_reports, stored),
        )
        return stored

    def latest_report(self) -> ContractRegistryReport | None:
        rows = self._list(
            aion_contract_registry_reports,
            ContractRegistryReport,
            {},
            "created_at",
            1,
        )
        return rows[0] if rows else None

    def list_reports(
        self,
        *,
        status: str | None = None,
        limit: int = 100,
    ) -> list[ContractRegistryReport]:
        return self._list(
            aion_contract_registry_reports,
            ContractRegistryReport,
            {"status": status},
            "created_at",
            limit,
        )

    def list_registry_records(self, *, limit: int = 100) -> list[dict[str, Any]]:
        """Expose local registry artifacts to the global resource registry."""
        records: list[dict[str, Any]] = []
        records.extend(
            _registry_record(
                "contract_snapshot",
                item.contract_snapshot_id,
                item.status,
                item.created_at,
                {
                    "snapshot_type": item.snapshot_type,
                    "root_hash": item.root_hash,
                    "contract_count": item.contract_count,
                    "interface_count": item.interface_count,
                },
            )
            for item in self.list_snapshots(limit=limit)
        )
        records.extend(
            _registry_record(
                "compatibility_scan",
                item.compatibility_scan_id,
                item.status,
                item.created_at,
                {
                    "breaking_count": item.breaking_count,
                    "warning_count": item.warning_count,
                    "findings_count": item.findings_count,
                },
            )
            for item in self.list_scans(limit=limit)
        )
        records.extend(
            _registry_record(
                "interface_drift",
                item.drift_finding_id,
                item.status,
                item.created_at,
                {
                    "finding_type": item.finding_type,
                    "severity": item.severity,
                    "breaking": item.breaking,
                    "interface_key": item.interface_key,
                },
            )
            for item in self.list_findings(limit=limit)
        )
        records.extend(
            _registry_record(
                "migration_note",
                item.migration_note_id,
                item.status,
                item.created_at,
                {
                    "note_type": item.note_type,
                    "compatibility_scan_id": item.compatibility_scan_id,
                    "finding_id": item.finding_id,
                },
            )
            for item in self.list_migration_notes(limit=limit)
        )
        records.extend(
            _registry_record(
                "contract_report",
                item.contract_report_id,
                item.status,
                item.created_at,
                {
                    "snapshot_id": item.snapshot_id,
                    "latest_scan_id": item.latest_scan_id,
                    "active_breaking_findings": item.active_breaking_findings,
                    "active_warning_findings": item.active_warning_findings,
                },
            )
            for item in self.list_reports(limit=limit)
        )
        return records[:limit]

    def _replace(
        self,
        table: Table,
        key_column: str,
        key_value: str,
        values: dict[str, Any],
    ) -> None:
        self._ensure_schema()
        with self._engine.begin() as connection:
            existing = connection.execute(
                select(table.c[key_column]).where(table.c[key_column] == key_value)
            ).first()
            if existing is None:
                connection.execute(insert(table).values(**values))
            else:
                connection.execute(
                    update(table).where(table.c[key_column] == key_value).values(**values)
                )

    def _get[T](
        self,
        table: Table,
        key_column: str,
        key_value: str,
        model: type[T],
    ) -> T | None:
        self._ensure_schema()
        with self._engine.connect() as connection:
            row = (
                connection.execute(select(table).where(table.c[key_column] == key_value))
                .mappings()
                .first()
            )
        return _row_to_model(row, model) if row is not None else None

    def _list[T](
        self,
        table: Table,
        model: type[T],
        filters: dict[str, object | None],
        order_column: str,
        limit: int,
    ) -> list[T]:
        self._ensure_schema()
        statement = select(table).order_by(getattr(table.c, order_column).desc()).limit(limit)
        for column, value in filters.items():
            if value is not None:
                statement = statement.where(getattr(table.c, column) == value)
        with self._engine.connect() as connection:
            rows = connection.execute(statement).mappings().all()
        return [_row_to_model(row, model) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready or not self._auto_create:
            return
        contract_registry_metadata.create_all(self._engine)
        self._schema_ready = True


def _model_values(table: Table, model: Any) -> dict[str, Any]:
    python_data = model.model_dump(mode="python")
    json_data = model.model_dump(mode="json")
    values: dict[str, Any] = {}
    for column in table.columns:
        if column.name not in python_data:
            continue
        value = python_data[column.name]
        values[column.name] = json_data[column.name] if isinstance(value, (dict, list)) else value
    return values


def _row_to_model[T](row: RowMapping, model: type[T]) -> T:
    return model(**dict(row))


def _registry_record(
    resource_type: str,
    resource_id: str,
    status: str,
    created_at: datetime | None,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    registry_metadata = dict(metadata)
    registry_metadata["contract_registry_status"] = status
    return {
        "resource_type": resource_type,
        "resource_id": resource_id,
        "status": _resource_registry_status(status),
        "created_at": created_at,
        "metadata": registry_metadata,
        "source_records_mutated": False,
    }


def _resource_registry_status(status: str) -> str:
    if status in {"archived", "deleted", "stale", "missing", "unknown"}:
        return status
    return "active"


__all__ = [
    "ContractRegistryRepository",
    "aion_compatibility_rules",
    "aion_compatibility_scans",
    "aion_contract_index_records",
    "aion_contract_registry_reports",
    "aion_contract_snapshots",
    "aion_interface_drift_findings",
    "aion_interface_inventory_records",
    "aion_migration_notes",
    "contract_registry_metadata",
]
