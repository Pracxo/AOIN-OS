"""Persistent repository for prompt governance records."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    Index,
    Integer,
    MetaData,
    Table,
    Text,
    UniqueConstraint,
    create_engine,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine import Engine, RowMapping
from sqlalchemy.pool import QueuePool, StaticPool

from aion_brain.contracts.model_inputs import ModelInputManifest
from aion_brain.contracts.prompts import (
    PromptBoundaryCheck,
    PromptFragment,
    PromptInjectionFinding,
    PromptPacket,
    PromptSection,
    PromptTemplate,
)

prompt_metadata = MetaData()
json_payload_type = JSON().with_variant(JSONB(), "postgresql")

aion_prompt_templates = Table(
    "aion_prompt_templates",
    prompt_metadata,
    Column("prompt_template_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("template_type", Text, nullable=False),
    Column("version", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("sections", json_payload_type, nullable=False),
    Column("required_inputs", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    UniqueConstraint("name", "version", name="uq_aion_prompt_templates_name_version"),
    Index("ix_aion_prompt_templates_name", "name"),
    Index("ix_aion_prompt_templates_status", "status"),
    Index("ix_aion_prompt_templates_template_type", "template_type"),
    Index("ix_aion_prompt_templates_version", "version"),
    Index("ix_aion_prompt_templates_created_at", "created_at"),
)

aion_prompt_fragments = Table(
    "aion_prompt_fragments",
    prompt_metadata,
    Column("prompt_fragment_id", Text, primary_key=True),
    Column("name", Text, nullable=False),
    Column("description", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("fragment_type", Text, nullable=False),
    Column("content", Text, nullable=False),
    Column("content_hash", Text, nullable=False),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("updated_at", DateTime(timezone=True), nullable=False),
    Column("disabled_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_prompt_fragments_name", "name"),
    Index("ix_aion_prompt_fragments_status", "status"),
    Index("ix_aion_prompt_fragments_fragment_type", "fragment_type"),
    Index("ix_aion_prompt_fragments_content_hash", "content_hash"),
    Index("ix_aion_prompt_fragments_created_at", "created_at"),
)

aion_prompt_packets = Table(
    "aion_prompt_packets",
    prompt_metadata,
    Column("prompt_packet_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("actor_id", Text, nullable=True),
    Column("workspace_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("packet_type", Text, nullable=False),
    Column("prompt_template_id", Text, nullable=True),
    Column("target_model_route", Text, nullable=True),
    Column("owner_scope", json_payload_type, nullable=False),
    Column("input_refs", json_payload_type, nullable=False),
    Column("section_manifests", json_payload_type, nullable=False),
    Column("rendered_hash", Text, nullable=False),
    Column("redacted_preview", Text, nullable=True),
    Column("token_estimate", Integer, nullable=False),
    Column("char_count", Integer, nullable=False),
    Column("boundary_check_id", Text, nullable=True),
    Column("grounding_verification_id", Text, nullable=True),
    Column("instruction_resolution_id", Text, nullable=True),
    Column("constraints", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("deleted_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_prompt_packets_trace_id", "trace_id"),
    Index("ix_aion_prompt_packets_actor_id", "actor_id"),
    Index("ix_aion_prompt_packets_workspace_id", "workspace_id"),
    Index("ix_aion_prompt_packets_status", "status"),
    Index("ix_aion_prompt_packets_packet_type", "packet_type"),
    Index("ix_aion_prompt_packets_prompt_template_id", "prompt_template_id"),
    Index("ix_aion_prompt_packets_target_model_route", "target_model_route"),
    Index("ix_aion_prompt_packets_rendered_hash", "rendered_hash"),
    Index("ix_aion_prompt_packets_boundary_check_id", "boundary_check_id"),
    Index("ix_aion_prompt_packets_grounding_verification_id", "grounding_verification_id"),
    Index("ix_aion_prompt_packets_instruction_resolution_id", "instruction_resolution_id"),
    Index("ix_aion_prompt_packets_created_at", "created_at"),
    Index("ix_aion_prompt_packets_deleted_at", "deleted_at"),
)

aion_prompt_boundary_checks = Table(
    "aion_prompt_boundary_checks",
    prompt_metadata,
    Column("boundary_check_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("safe", Boolean, nullable=False),
    Column("injection_findings", json_payload_type, nullable=False),
    Column("blocked_sections", json_payload_type, nullable=False),
    Column("warnings", json_payload_type, nullable=False),
    Column("constraints", json_payload_type, nullable=False),
    Column("score", Float, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_by", Text, nullable=True),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_prompt_boundary_checks_trace_id", "trace_id"),
    Index("ix_aion_prompt_boundary_checks_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_prompt_boundary_checks_status", "status"),
    Index("ix_aion_prompt_boundary_checks_safe", "safe"),
    Index("ix_aion_prompt_boundary_checks_score", "score"),
    Index("ix_aion_prompt_boundary_checks_created_at", "created_at"),
)

aion_prompt_injection_findings = Table(
    "aion_prompt_injection_findings",
    prompt_metadata,
    Column("injection_finding_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=True),
    Column("source_type", Text, nullable=False),
    Column("source_id", Text, nullable=True),
    Column("finding_type", Text, nullable=False),
    Column("severity", Text, nullable=False),
    Column("status", Text, nullable=False),
    Column("matched_text_redacted", Text, nullable=False),
    Column("reason", Text, nullable=False),
    Column("recommended_action", Text, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("resolved_at", DateTime(timezone=True), nullable=True),
    Index("ix_aion_prompt_injection_findings_trace_id", "trace_id"),
    Index("ix_aion_prompt_injection_findings_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_prompt_injection_findings_source_type", "source_type"),
    Index("ix_aion_prompt_injection_findings_source_id", "source_id"),
    Index("ix_aion_prompt_injection_findings_finding_type", "finding_type"),
    Index("ix_aion_prompt_injection_findings_severity", "severity"),
    Index("ix_aion_prompt_injection_findings_status", "status"),
    Index("ix_aion_prompt_injection_findings_created_at", "created_at"),
)

aion_model_input_manifests = Table(
    "aion_model_input_manifests",
    prompt_metadata,
    Column("model_input_manifest_id", Text, primary_key=True),
    Column("trace_id", Text, nullable=True),
    Column("prompt_packet_id", Text, nullable=False),
    Column("model_route", Text, nullable=True),
    Column("provider_type", Text, nullable=True),
    Column("status", Text, nullable=False),
    Column("input_hash", Text, nullable=False),
    Column("section_count", Integer, nullable=False),
    Column("token_estimate", Integer, nullable=False),
    Column("context_budget", json_payload_type, nullable=False),
    Column("grounding_refs", json_payload_type, nullable=False),
    Column("instruction_refs", json_payload_type, nullable=False),
    Column("safety_refs", json_payload_type, nullable=False),
    Column("metadata", json_payload_type, nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Index("ix_aion_model_input_manifests_trace_id", "trace_id"),
    Index("ix_aion_model_input_manifests_prompt_packet_id", "prompt_packet_id"),
    Index("ix_aion_model_input_manifests_model_route", "model_route"),
    Index("ix_aion_model_input_manifests_provider_type", "provider_type"),
    Index("ix_aion_model_input_manifests_status", "status"),
    Index("ix_aion_model_input_manifests_input_hash", "input_hash"),
    Index("ix_aion_model_input_manifests_created_at", "created_at"),
)


class PromptRepository:
    """Repository for prompt governance contracts."""

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

    def save_template(self, template: PromptTemplate) -> PromptTemplate:
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = template.model_copy(
            update={"created_at": template.created_at or now, "updated_at": now}
        )
        with self._engine.begin() as connection:
            connection.execute(insert(aion_prompt_templates).values(**_template_values(stored)))
        return stored

    def get_template(self, prompt_template_id: str) -> PromptTemplate | None:
        self._ensure_schema()
        statement = select(aion_prompt_templates).where(
            aion_prompt_templates.c.prompt_template_id == prompt_template_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_template(row) if row is not None else None

    def list_templates(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        template_type: str | None = None,
        limit: int = 100,
    ) -> list[PromptTemplate]:
        self._ensure_schema()
        statement = select(aion_prompt_templates).order_by(
            aion_prompt_templates.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_prompt_templates.c.status == status)
        if template_type is not None:
            statement = statement.where(aion_prompt_templates.c.template_type == template_type)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [
            template
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            for template in [_row_to_template(row)]
        ]

    def disable_template(
        self,
        prompt_template_id: str,
        *,
        reason: str,
        actor_id: str | None,
    ) -> PromptTemplate | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        template = self.get_template(prompt_template_id)
        if template is None:
            return None
        metadata = {**template.metadata, "disabled_reason": reason, "disabled_by": actor_id}
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_prompt_templates)
                .where(aion_prompt_templates.c.prompt_template_id == prompt_template_id)
                .values(status="disabled", metadata=metadata, updated_at=now, disabled_at=now)
            )
        return template.model_copy(
            update={
                "status": "disabled",
                "metadata": metadata,
                "updated_at": now,
                "disabled_at": now,
            }
        )

    def save_fragment(self, fragment: PromptFragment) -> PromptFragment:
        self._ensure_schema()
        now = datetime.now(UTC)
        stored = fragment.model_copy(
            update={"created_at": fragment.created_at or now, "updated_at": now}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_prompt_fragments).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_fragments(
        self,
        scope: list[str],
        *,
        status: str | None = None,
        fragment_type: str | None = None,
        limit: int = 100,
    ) -> list[PromptFragment]:
        self._ensure_schema()
        statement = select(aion_prompt_fragments).order_by(
            aion_prompt_fragments.c.created_at.desc()
        )
        if status is not None:
            statement = statement.where(aion_prompt_fragments.c.status == status)
        if fragment_type is not None:
            statement = statement.where(aion_prompt_fragments.c.fragment_type == fragment_type)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [
            fragment
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            for fragment in [_row_to_fragment(row)]
        ]

    def disable_fragment(
        self,
        prompt_fragment_id: str,
        *,
        reason: str,
        actor_id: str | None,
    ) -> PromptFragment | None:
        self._ensure_schema()
        now = datetime.now(UTC)
        statement = select(aion_prompt_fragments).where(
            aion_prompt_fragments.c.prompt_fragment_id == prompt_fragment_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        if row is None:
            return None
        fragment = _row_to_fragment(row)
        metadata = {**fragment.metadata, "disabled_reason": reason, "disabled_by": actor_id}
        with self._engine.begin() as connection:
            connection.execute(
                update(aion_prompt_fragments)
                .where(aion_prompt_fragments.c.prompt_fragment_id == prompt_fragment_id)
                .values(status="disabled", metadata=metadata, updated_at=now, disabled_at=now)
            )
        return fragment.model_copy(
            update={
                "status": "disabled",
                "metadata": metadata,
                "updated_at": now,
                "disabled_at": now,
            }
        )

    def save_packet(self, packet: PromptPacket) -> PromptPacket:
        self._ensure_schema()
        stored = packet.model_copy(update={"created_at": packet.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(insert(aion_prompt_packets).values(**_packet_values(stored)))
        return stored

    def get_packet(self, prompt_packet_id: str) -> PromptPacket | None:
        self._ensure_schema()
        statement = select(aion_prompt_packets).where(
            aion_prompt_packets.c.prompt_packet_id == prompt_packet_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_packet(row) if row is not None else None

    def list_packets(
        self,
        scope: list[str],
        *,
        trace_id: str | None = None,
        status: str | None = None,
        packet_type: str | None = None,
        limit: int = 50,
    ) -> list[PromptPacket]:
        self._ensure_schema()
        statement = select(aion_prompt_packets).order_by(aion_prompt_packets.c.created_at.desc())
        if trace_id is not None:
            statement = statement.where(aion_prompt_packets.c.trace_id == trace_id)
        if status is not None:
            statement = statement.where(aion_prompt_packets.c.status == status)
        if packet_type is not None:
            statement = statement.where(aion_prompt_packets.c.packet_type == packet_type)
        statement = statement.where(aion_prompt_packets.c.deleted_at.is_(None))
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [
            packet
            for row in rows
            if _scope_matches(list(row["owner_scope"]), scope)
            for packet in [_row_to_packet(row)]
        ]

    def delete_packet(self, prompt_packet_id: str) -> bool:
        """Soft delete one prompt packet."""

        self._ensure_schema()
        with self._engine.begin() as connection:
            result = connection.execute(
                update(aion_prompt_packets)
                .where(aion_prompt_packets.c.prompt_packet_id == prompt_packet_id)
                .values(deleted_at=datetime.now(UTC), status="archived")
            )
        return bool(result.rowcount)

    def save_boundary_check(self, check: PromptBoundaryCheck) -> PromptBoundaryCheck:
        self._ensure_schema()
        stored = check.model_copy(update={"created_at": check.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_prompt_boundary_checks).values(**_boundary_values(stored))
            )
        return stored

    def get_boundary_check(self, boundary_check_id: str) -> PromptBoundaryCheck | None:
        self._ensure_schema()
        statement = select(aion_prompt_boundary_checks).where(
            aion_prompt_boundary_checks.c.boundary_check_id == boundary_check_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_boundary(row) if row is not None else None

    def save_injection_finding(
        self,
        finding: PromptInjectionFinding,
    ) -> PromptInjectionFinding:
        self._ensure_schema()
        stored = finding.model_copy(update={"created_at": finding.created_at or datetime.now(UTC)})
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_prompt_injection_findings).values(**stored.model_dump(mode="python"))
            )
        return stored

    def list_injection_findings(
        self,
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        severity: str | None = None,
        status: str | None = None,
        limit: int = 100,
    ) -> list[PromptInjectionFinding]:
        self._ensure_schema()
        statement = select(aion_prompt_injection_findings).order_by(
            aion_prompt_injection_findings.c.created_at.desc()
        )
        if trace_id is not None:
            statement = statement.where(aion_prompt_injection_findings.c.trace_id == trace_id)
        if prompt_packet_id is not None:
            statement = statement.where(
                aion_prompt_injection_findings.c.prompt_packet_id == prompt_packet_id
            )
        if severity is not None:
            statement = statement.where(aion_prompt_injection_findings.c.severity == severity)
        if status is not None:
            statement = statement.where(aion_prompt_injection_findings.c.status == status)
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_finding(row) for row in rows]

    def save_manifest(self, manifest: ModelInputManifest) -> ModelInputManifest:
        self._ensure_schema()
        stored = manifest.model_copy(
            update={"created_at": manifest.created_at or datetime.now(UTC)}
        )
        with self._engine.begin() as connection:
            connection.execute(
                insert(aion_model_input_manifests).values(**stored.model_dump(mode="python"))
            )
        return stored

    def get_manifest(self, model_input_manifest_id: str) -> ModelInputManifest | None:
        self._ensure_schema()
        statement = select(aion_model_input_manifests).where(
            aion_model_input_manifests.c.model_input_manifest_id == model_input_manifest_id
        )
        with self._engine.connect() as connection:
            row = connection.execute(statement).mappings().first()
        return _row_to_manifest(row) if row is not None else None

    def list_manifests(
        self,
        *,
        trace_id: str | None = None,
        prompt_packet_id: str | None = None,
        limit: int = 50,
    ) -> list[ModelInputManifest]:
        self._ensure_schema()
        statement = select(aion_model_input_manifests).order_by(
            aion_model_input_manifests.c.created_at.desc()
        )
        if trace_id is not None:
            statement = statement.where(aion_model_input_manifests.c.trace_id == trace_id)
        if prompt_packet_id is not None:
            statement = statement.where(
                aion_model_input_manifests.c.prompt_packet_id == prompt_packet_id
            )
        with self._engine.connect() as connection:
            rows = connection.execute(statement.limit(limit)).mappings().all()
        return [_row_to_manifest(row) for row in rows]

    def _ensure_schema(self) -> None:
        if self._schema_ready:
            return
        if self._auto_create:
            prompt_metadata.create_all(self._engine)
        self._schema_ready = True


def _template_values(template: PromptTemplate) -> dict[str, Any]:
    values = template.model_dump(mode="python")
    values["sections"] = [section.model_dump(mode="python") for section in template.sections]
    return values


def _packet_values(packet: PromptPacket) -> dict[str, Any]:
    return {
        "prompt_packet_id": packet.prompt_packet_id,
        "trace_id": packet.trace_id,
        "actor_id": packet.actor_id,
        "workspace_id": packet.workspace_id,
        "status": packet.status,
        "packet_type": packet.packet_type,
        "prompt_template_id": packet.prompt_template_id,
        "target_model_route": packet.target_model_route,
        "owner_scope": packet.owner_scope,
        "input_refs": packet.input_refs,
        "section_manifests": packet.section_manifests,
        "rendered_hash": packet.rendered_hash,
        "redacted_preview": packet.redacted_preview,
        "token_estimate": packet.token_estimate,
        "char_count": packet.char_count,
        "boundary_check_id": packet.boundary_check_id,
        "grounding_verification_id": packet.grounding_verification_id,
        "instruction_resolution_id": packet.instruction_resolution_id,
        "constraints": packet.constraints,
        "metadata": packet.metadata,
        "created_by": packet.created_by,
        "created_at": packet.created_at,
        "deleted_at": packet.deleted_at,
    }


def _boundary_values(check: PromptBoundaryCheck) -> dict[str, Any]:
    values = check.model_dump(mode="python")
    values["injection_findings"] = [
        finding.model_dump(mode="json") for finding in check.injection_findings
    ]
    return values


def _row_to_template(row: RowMapping) -> PromptTemplate:
    values = dict(row)
    values["sections"] = [PromptSection(**item) for item in values.get("sections", [])]
    return PromptTemplate(**values)


def _row_to_fragment(row: RowMapping) -> PromptFragment:
    return PromptFragment(**dict(row))


def _row_to_packet(row: RowMapping) -> PromptPacket:
    values = dict(row)
    values["sections"] = []
    return PromptPacket(**values)


def _row_to_boundary(row: RowMapping) -> PromptBoundaryCheck:
    values = dict(row)
    values["injection_findings"] = [
        PromptInjectionFinding(**item) for item in values.get("injection_findings", [])
    ]
    return PromptBoundaryCheck(**values)


def _row_to_finding(row: RowMapping) -> PromptInjectionFinding:
    return PromptInjectionFinding(**dict(row))


def _row_to_manifest(row: RowMapping) -> ModelInputManifest:
    return ModelInputManifest(**dict(row))


def _scope_matches(record_scope: list[str], requested_scope: list[str]) -> bool:
    return bool(set(record_scope) & set(requested_scope))


__all__ = [
    "PromptRepository",
    "aion_model_input_manifests",
    "aion_prompt_boundary_checks",
    "aion_prompt_fragments",
    "aion_prompt_injection_findings",
    "aion_prompt_packets",
    "aion_prompt_templates",
    "prompt_metadata",
]
