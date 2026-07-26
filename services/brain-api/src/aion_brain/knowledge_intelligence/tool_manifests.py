"""Versioned in-memory tool manifest registry for AION-215."""

from __future__ import annotations

from collections.abc import Iterable

from aion_brain.contracts.knowledge_tool_verification import (
    APPROVAL_RECORD_ID,
    AUTHORIZATION_SCOPE,
    AUTHORIZATION_TRANSACTION_ID,
    FORMAL_CLOSEOUT_TASK,
    IMPLEMENTATION_TASK,
    PROGRAM_ID,
    ToolCapabilityManifest,
    ToolEffectType,
    ToolManifestRegistrySnapshot,
    ToolOperationClass,
    ToolPermissionEnvelope,
    ToolRiskClass,
    ToolSchemaDescriptor,
    permission_envelope_fingerprint,
    schema_descriptor_fingerprint,
    tool_manifest_fingerprint,
    tool_registry_fingerprint,
)
from aion_brain.knowledge_intelligence.tool_effects import (
    build_expected_effect,
    default_forbidden_runtime_effects,
)


def build_schema_descriptor(
    *,
    schema_id: str,
    required_fields: tuple[str, ...],
    optional_fields: tuple[str, ...] = (),
    forbidden_fields: tuple[str, ...] = (),
    field_types: dict[str, str] | None = None,
) -> ToolSchemaDescriptor:
    """Build a strict fingerprinted schema descriptor."""

    payload = {
        "schema_version": "aion-knowledge-tool-schema-descriptor/v1",
        "schema_id": schema_id,
        "required_fields": required_fields,
        "optional_fields": optional_fields,
        "forbidden_fields": forbidden_fields,
        "field_types": field_types or {},
        "strict": True,
    }
    return ToolSchemaDescriptor.model_validate(
        {**payload, "schema_fingerprint": schema_descriptor_fingerprint(payload)}
    )


def build_permission_envelope(
    *,
    permission_ids: tuple[str, ...] = (),
    requires_local_fixture_read: bool = False,
    requires_filesystem_read: bool = False,
) -> ToolPermissionEnvelope:
    """Build a permission envelope with every runtime/write channel disabled."""

    payload = {
        "schema_version": "aion-knowledge-tool-permission-envelope/v1",
        "permission_ids": permission_ids,
        "requires_local_fixture_read": requires_local_fixture_read,
        "requires_filesystem_read": requires_filesystem_read,
        "requires_network": False,
        "requires_dns": False,
        "requires_shell": False,
        "requires_subprocess": False,
        "requires_browser": False,
        "requires_connector": False,
        "requires_model_provider": False,
        "requires_filesystem_write": False,
        "requires_source_write": False,
        "requires_git_write": False,
        "requires_deployment": False,
        "requires_approval_creation": False,
        "requires_persistence": False,
    }
    return ToolPermissionEnvelope.model_validate(
        {**payload, "permission_fingerprint": permission_envelope_fingerprint(payload)}
    )


def build_tool_manifest(
    *,
    manifest_id: str,
    tool_id: str,
    tool_version: str,
    operation_class: ToolOperationClass,
    risk_class: ToolRiskClass,
    input_schema: ToolSchemaDescriptor,
    output_schema: ToolSchemaDescriptor,
    permission_envelope: ToolPermissionEnvelope,
    declared_effect_type: ToolEffectType,
    declared_effect_scope: str,
) -> ToolCapabilityManifest:
    """Build an immutable synthetic tool capability manifest."""

    declared = (
        build_expected_effect(
            effect_id=f"effect-{manifest_id}-{declared_effect_type.value}",
            effect_type=declared_effect_type,
            effect_scope=declared_effect_scope,
            artifact_id=f"artifact-{manifest_id}",
        ),
    )
    payload = {
        "schema_version": "aion-knowledge-tool-manifest/v1",
        "program_id": PROGRAM_ID,
        "authorization_transaction_id": AUTHORIZATION_TRANSACTION_ID,
        "implementation_task": IMPLEMENTATION_TASK,
        "formal_closeout_task": FORMAL_CLOSEOUT_TASK,
        "authorization_scope": AUTHORIZATION_SCOPE,
        "manifest_id": manifest_id,
        "tool_id": tool_id,
        "tool_version": tool_version,
        "operation_class": operation_class,
        "risk_class": risk_class,
        "input_schema": input_schema,
        "output_schema": output_schema,
        "permission_envelope": permission_envelope,
        "declared_effects": declared,
        "prohibited_effects": default_forbidden_runtime_effects(),
        "deterministic_simulation_supported": True,
        "idempotency_supported": True,
        "rollback_supported": True,
        "compensation_supported": True,
        "synthetic": True,
        "read_only": True,
        "redacted": True,
        "actual_execution_enabled": False,
        "actual_tool_executed": False,
        "persistent_write_applied": False,
        "runtime_effect": False,
    }
    return ToolCapabilityManifest.model_validate(
        {**payload, "manifest_fingerprint": tool_manifest_fingerprint(payload)}
    )


class InMemoryToolManifestRegistry:
    """Per-instance versioned registry with no persistence backend."""

    def __init__(
        self,
        *,
        registry_id: str = "registry-aion-215-default",
        registry_version: int = 1,
        manifests: Iterable[ToolCapabilityManifest] = (),
    ) -> None:
        self.registry_id = registry_id
        self.registry_version = registry_version
        self._manifests = {manifest.manifest_id: manifest for manifest in manifests}

    def register(self, manifest: ToolCapabilityManifest) -> None:
        """Register a manifest in this in-memory instance only."""

        self._manifests[manifest.manifest_id] = manifest

    def snapshot(self) -> ToolManifestRegistrySnapshot:
        """Return a deterministic immutable registry snapshot."""

        manifests = tuple(self._manifests[key] for key in sorted(self._manifests))
        schema_by_id: dict[str, ToolSchemaDescriptor] = {}
        for manifest in manifests:
            schema_by_id[manifest.input_schema.schema_id] = manifest.input_schema
            schema_by_id[manifest.output_schema.schema_id] = manifest.output_schema
        schemas = tuple(schema_by_id[key] for key in sorted(schema_by_id))
        payload = {
            "schema_version": "aion-knowledge-tool-registry/v1",
            "registry_id": self.registry_id,
            "registry_version": self.registry_version,
            "manifests": manifests,
            "schemas": schemas,
            "in_memory_only": True,
            "persistent_write_applied": False,
            "runtime_effect": False,
        }
        return ToolManifestRegistrySnapshot.model_validate(
            {**payload, "registry_fingerprint": tool_registry_fingerprint(payload)}
        )

    def find(self, manifest_id: str) -> ToolCapabilityManifest | None:
        """Return a manifest by exact id."""

        return self._manifests.get(manifest_id)


def build_default_tool_manifest_registry() -> InMemoryToolManifestRegistry:
    """Build the deterministic AION-215 default synthetic manifest registry."""

    validation_input = build_schema_descriptor(
        schema_id="schema-synthetic-validation-input",
        required_fields=("artifact_kind", "content_fingerprint"),
        optional_fields=("plan_id", "case_id"),
        forbidden_fields=("credential", "token", "raw_prompt", "source_patch"),
        field_types={
            "artifact_kind": "str",
            "content_fingerprint": "str",
            "plan_id": "str",
            "case_id": "str",
        },
    )
    validation_output = build_schema_descriptor(
        schema_id="schema-synthetic-validation-output",
        required_fields=("status", "input_fingerprint", "tool_id", "validated"),
        optional_fields=("plan_id",),
        forbidden_fields=("credential", "token", "raw_prompt", "source_patch"),
        field_types={
            "status": "str",
            "input_fingerprint": "str",
            "tool_id": "str",
            "validated": "bool",
            "plan_id": "str",
        },
    )
    parser_input = build_schema_descriptor(
        schema_id="schema-synthetic-parser-input",
        required_fields=("artifact_kind", "content_fingerprint"),
        optional_fields=("parse_mode",),
        forbidden_fields=("credential", "token", "raw_prompt", "source_patch"),
        field_types={
            "artifact_kind": "str",
            "content_fingerprint": "str",
            "parse_mode": "str",
        },
    )
    fixture_input = build_schema_descriptor(
        schema_id="schema-synthetic-fixture-read-input",
        required_fields=("fixture_fingerprint", "case_id"),
        optional_fields=("record_count",),
        forbidden_fields=("credential", "token", "raw_prompt", "source_patch"),
        field_types={
            "fixture_fingerprint": "str",
            "case_id": "str",
            "record_count": "int",
        },
    )
    no_permissions = build_permission_envelope()
    fixture_permissions = build_permission_envelope(
        permission_ids=("explicit-local-fixture-read",),
        requires_local_fixture_read=True,
        requires_filesystem_read=True,
    )
    manifests = (
        build_tool_manifest(
            manifest_id="manifest-synthetic-json-parser",
            tool_id="synthetic.json-parser",
            tool_version="1.0.0",
            operation_class=ToolOperationClass.DETERMINISTIC_PARSER,
            risk_class=ToolRiskClass.MINIMAL,
            input_schema=parser_input,
            output_schema=validation_output,
            permission_envelope=no_permissions,
            declared_effect_type=ToolEffectType.PARSE,
            declared_effect_scope="synthetic-artifact",
        ),
        build_tool_manifest(
            manifest_id="manifest-synthetic-json-validator",
            tool_id="synthetic.json-validator",
            tool_version="1.0.0",
            operation_class=ToolOperationClass.DETERMINISTIC_VALIDATOR,
            risk_class=ToolRiskClass.LOW,
            input_schema=validation_input,
            output_schema=validation_output,
            permission_envelope=no_permissions,
            declared_effect_type=ToolEffectType.VALIDATE,
            declared_effect_scope="synthetic-artifact",
        ),
        build_tool_manifest(
            manifest_id="manifest-synthetic-fixture-reader",
            tool_id="synthetic.fixture-reader",
            tool_version="1.0.0",
            operation_class=ToolOperationClass.LOCAL_FIXTURE_READ,
            risk_class=ToolRiskClass.MODERATE,
            input_schema=fixture_input,
            output_schema=validation_output,
            permission_envelope=fixture_permissions,
            declared_effect_type=ToolEffectType.READ,
            declared_effect_scope="explicit-local-fixture",
        ),
    )
    return InMemoryToolManifestRegistry(manifests=manifests)


__all__ = [
    "APPROVAL_RECORD_ID",
    "InMemoryToolManifestRegistry",
    "build_default_tool_manifest_registry",
    "build_permission_envelope",
    "build_schema_descriptor",
    "build_tool_manifest",
]
