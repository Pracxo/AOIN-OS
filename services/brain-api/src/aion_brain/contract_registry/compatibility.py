"""Deterministic interface compatibility scanner."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from aion_brain.contract_registry.redaction import contains_disallowed_domain_term
from aion_brain.contracts.compatibility import (
    CompatibilityRule,
    CompatibilityScan,
    CompatibilityScanRequest,
    CompatibilityScanStatus,
    InterfaceDriftFinding,
)
from aion_brain.contracts.contract_registry import ContractSnapshot
from aion_brain.contracts.scopes import ActorContext
from aion_brain.dialogue._shared import authorize, emit_telemetry


class CompatibilityScanner:
    """Compare contract snapshots and report interface drift."""

    def __init__(
        self,
        repository: object,
        snapshot_service: object,
        rule_service: object,
        policy_adapter: object | None,
        *,
        migration_note_service: object | None = None,
        notification_router: object | None = None,
        telemetry_service: object | None = None,
        audit_sink: object | None = None,
        provenance_service: object | None = None,
        actor_context: ActorContext | None = None,
    ) -> None:
        self._repository = repository
        self._snapshot_service = snapshot_service
        self._rule_service = rule_service
        self._policy_adapter = policy_adapter
        self._migration_note_service = migration_note_service
        self._notification_router = notification_router
        self._telemetry_service = telemetry_service
        self._audit_sink = audit_sink
        self._provenance_service = provenance_service
        self._actor_context = actor_context or ActorContext()

    def with_actor_context(self, actor_context: ActorContext) -> CompatibilityScanner:
        return CompatibilityScanner(
            self._repository,
            self._snapshot_service,
            self._rule_service,
            self._policy_adapter,
            migration_note_service=self._migration_note_service,
            notification_router=self._notification_router,
            telemetry_service=self._telemetry_service,
            audit_sink=self._audit_sink,
            provenance_service=self._provenance_service,
            actor_context=actor_context,
        )

    def scan(self, request: CompatibilityScanRequest) -> CompatibilityScan:
        try:
            authorize(
                self._policy_adapter,
                action_type="contract_registry.compatibility.scan",
                resource_type="compatibility_scan",
                resource_id=request.compatibility_scan_id,
                scope=request.owner_scope,
                trace_id=request.trace_id or self._actor_context.trace_id,
                actor_id=request.actor_id or self._actor_context.actor_id,
                workspace_id=request.workspace_id or self._actor_context.workspace_id,
                risk_level="medium",
                context={"mode": request.mode, "source_mutated": False},
            )
        except PermissionError:
            return _blocked_scan(request, self._actor_context)

        scan_id = request.compatibility_scan_id or f"compatibility-scan-{uuid4().hex}"
        emit_telemetry(
            self._telemetry_service,
            event_type="compatibility_scan_started",
            node_type="compatibility_scan",
            node_id=scan_id,
            intensity=0.4,
            trace_id=request.trace_id or self._actor_context.trace_id,
            payload={"mode": request.mode},
        )

        baseline = self._snapshot(request.baseline_snapshot_id, request.owner_scope, "baseline")
        candidate = self._snapshot(
            request.candidate_snapshot_id, request.owner_scope, "post_change"
        )
        rules = self._rules(request.owner_scope, request.rule_ids)
        findings = _compare_snapshots(scan_id, request.trace_id, baseline, candidate)
        rules_applied = [str(rule.rule_type) for rule in rules] or ["built_in"]
        breaking_count = sum(1 for item in findings if item.breaking)
        warning_count = sum(1 for item in findings if not item.breaking)
        status = _status(request.mode, breaking_count, warning_count)
        scan = CompatibilityScan(
            compatibility_scan_id=scan_id,
            trace_id=request.trace_id or self._actor_context.trace_id,
            actor_id=request.actor_id or self._actor_context.actor_id,
            workspace_id=request.workspace_id or self._actor_context.workspace_id,
            status=status,
            mode=request.mode,
            owner_scope=request.owner_scope,
            baseline_snapshot_id=baseline.contract_snapshot_id if baseline else None,
            candidate_snapshot_id=candidate.contract_snapshot_id if candidate else None,
            scan_scope=request.scan_scope,
            rules_applied=rules_applied,
            findings_count=len(findings),
            breaking_count=breaking_count,
            warning_count=warning_count,
            passed_count=max(0, len(rules_applied) - len(findings)),
            findings=findings,
            result={
                "source_mutated": False,
                "code_generated": False,
                "external_calls": False,
            },
            metadata=request.metadata,
            created_by=request.created_by or self._actor_context.actor_id,
            created_at=datetime.now(UTC),
            completed_at=datetime.now(UTC),
        )
        save_scan = getattr(self._repository, "save_scan", None)
        stored = save_scan(scan) if callable(save_scan) else scan
        if request.mode == "controlled":
            self._persist_findings(stored.findings, request)
        if request.create_notifications:
            _publish_notification(self._notification_router, stored)
        _record_audit(
            self._audit_sink, "compatibility_scan_completed", stored.compatibility_scan_id
        )
        _record_provenance(
            self._provenance_service,
            stored.compatibility_scan_id,
            [
                value
                for value in (stored.baseline_snapshot_id, stored.candidate_snapshot_id)
                if value
            ],
        )
        emit_telemetry(
            self._telemetry_service,
            event_type="compatibility_scan_completed",
            node_type="compatibility_scan",
            node_id=stored.compatibility_scan_id,
            intensity=1.0 if stored.breaking_count else 0.7 if stored.warning_count else 0.4,
            trace_id=stored.trace_id,
            payload={
                "breaking_count": stored.breaking_count,
                "warning_count": stored.warning_count,
            },
        )
        for finding in stored.findings:
            emit_telemetry(
                self._telemetry_service,
                event_type="interface_drift_detected",
                node_type="interface_drift",
                node_id=finding.drift_finding_id,
                intensity=1.0 if finding.severity in {"high", "critical"} else 0.7,
                trace_id=finding.trace_id,
                payload={"finding_type": finding.finding_type, "breaking": finding.breaking},
            )
        return stored

    def _snapshot(
        self,
        snapshot_id: str | None,
        scope: list[str],
        fallback_type: str,
    ) -> ContractSnapshot | None:
        if snapshot_id:
            get_snapshot = getattr(self._snapshot_service, "get_snapshot", None)
            snapshot = get_snapshot(snapshot_id, scope) if callable(get_snapshot) else None
            return snapshot if isinstance(snapshot, ContractSnapshot) else None
        create_snapshot = getattr(self._snapshot_service, "create_snapshot", None)
        snapshot = create_snapshot(scope, fallback_type) if callable(create_snapshot) else None
        return snapshot if isinstance(snapshot, ContractSnapshot) else None

    def _rules(self, scope: list[str], rule_ids: list[str]) -> list[CompatibilityRule]:
        list_rules = getattr(self._rule_service, "list_rules", None)
        rules = list_rules(scope, status="active", limit=500) if callable(list_rules) else []
        typed = [rule for rule in rules if isinstance(rule, CompatibilityRule)]
        if not rule_ids:
            return typed
        return [rule for rule in typed if rule.compatibility_rule_id in set(rule_ids)]

    def _persist_findings(
        self,
        findings: list[InterfaceDriftFinding],
        request: CompatibilityScanRequest,
    ) -> None:
        save_finding = getattr(self._repository, "save_finding", None)
        for finding in findings:
            stored = save_finding(finding) if callable(save_finding) else finding
            create_note = getattr(self._migration_note_service, "create_from_finding", None)
            if callable(create_note):
                create_note(stored, request.owner_scope, request.created_by)


def _compare_snapshots(
    scan_id: str,
    trace_id: str | None,
    baseline: ContractSnapshot | None,
    candidate: ContractSnapshot | None,
) -> list[InterfaceDriftFinding]:
    if baseline is None or candidate is None:
        return [
            _finding(
                scan_id,
                trace_id,
                "generic",
                "generic",
                None,
                None,
                "contract_registry",
                "medium",
                False,
                "Snapshot unavailable",
                "A baseline or candidate snapshot was unavailable.",
                "Create both snapshots and rerun the compatibility scan.",
            )
        ]
    findings: list[InterfaceDriftFinding] = []
    old_interfaces = _by_key(_manifest_items(baseline, "interfaces"), "interface_key")
    new_interfaces = _by_key(_manifest_items(candidate, "interfaces"), "interface_key")
    old_contracts = _by_key(_manifest_items(baseline, "contracts"), "contract_key")
    new_contracts = _by_key(_manifest_items(candidate, "contracts"), "contract_key")

    for key, old in old_interfaces.items():
        if key in new_interfaces:
            continue
        finding_type, severity, breaking, action = _removed_interface_kind(old)
        findings.append(
            _finding(
                scan_id,
                trace_id,
                finding_type,
                str(old.get("interface_type") or "generic"),
                None,
                key,
                str(old.get("source_system") or "unknown"),
                severity,
                breaking,
                f"Removed interface {key}",
                f"Interface {key} existed in the baseline but not in the candidate.",
                action,
                old_ref=baseline.contract_snapshot_id,
                new_ref=candidate.contract_snapshot_id,
            )
        )

    for key, old in old_contracts.items():
        new = new_contracts.get(key)
        if new is None:
            findings.append(
                _finding(
                    scan_id,
                    trace_id,
                    "removed_contract",
                    "pydantic_model",
                    key,
                    None,
                    "contracts",
                    "high",
                    True,
                    f"Removed contract {key}",
                    f"Contract {key} existed in the baseline but not in the candidate.",
                    "Restore the contract or publish a migration note.",
                )
            )
            continue
        findings.extend(_contract_schema_findings(scan_id, trace_id, key, old, new))

    findings.extend(_missing_binding_findings(scan_id, trace_id, candidate, new_interfaces))
    findings.extend(_payload_safety_findings(scan_id, trace_id, candidate))
    return sorted(
        findings,
        key=lambda item: (item.finding_type, item.interface_key or item.contract_key or ""),
    )


def _contract_schema_findings(
    scan_id: str,
    trace_id: str | None,
    key: str,
    old: dict[str, Any],
    new: dict[str, Any],
) -> list[InterfaceDriftFinding]:
    findings: list[InterfaceDriftFinding] = []
    old_schema = _schema(old)
    new_schema = _schema(new)
    old_required = set(_required_fields(old_schema))
    new_required = set(_required_fields(new_schema))
    added_required = sorted(new_required - old_required)
    if added_required:
        findings.append(
            _finding(
                scan_id,
                trace_id,
                "required_field_added",
                "pydantic_model",
                key,
                None,
                "contracts",
                "high",
                True,
                f"Required field added to {key}",
                f"Candidate added required fields: {', '.join(added_required)}.",
                "Make new fields optional or provide a migration note.",
            )
        )
    removed = sorted(set(_properties(old_schema)) - set(_properties(new_schema)))
    for field in removed:
        findings.append(
            _finding(
                scan_id,
                trace_id,
                "removed_field",
                "pydantic_model",
                key,
                None,
                "contracts",
                "high",
                True,
                f"Removed field {field}",
                f"Field {field} was removed from {key}.",
                "Restore the field or publish a migration path.",
            )
        )
    for field in sorted(set(_properties(old_schema)).intersection(_properties(new_schema))):
        old_type = _properties(old_schema)[field].get("type")
        new_type = _properties(new_schema)[field].get("type")
        if old_type and new_type and old_type != new_type:
            findings.append(
                _finding(
                    scan_id,
                    trace_id,
                    "type_changed",
                    "pydantic_model",
                    key,
                    None,
                    "contracts",
                    "high",
                    True,
                    f"Field type changed for {field}",
                    f"Field {field} changed type from {old_type} to {new_type}.",
                    "Keep the old type compatible or publish a migration path.",
                )
            )
    if (
        old.get("schema_hash") != new.get("schema_hash")
        and not findings
        and not _is_non_breaking_schema_change(old_schema, new_schema)
    ):
        findings.append(
            _finding(
                scan_id,
                trace_id,
                "schema_hash_changed",
                "pydantic_model",
                key,
                None,
                "contracts",
                "low",
                False,
                f"Schema hash changed for {key}",
                f"Schema hash changed for {key} without a detected breaking change.",
                "Review and document the non-breaking schema change.",
            )
        )
    return findings


def _is_non_breaking_schema_change(
    old_schema: dict[str, Any],
    new_schema: dict[str, Any],
) -> bool:
    old_properties = _properties(old_schema)
    new_properties = _properties(new_schema)
    old_required = set(_required_fields(old_schema))
    new_required = set(_required_fields(new_schema))
    if not set(old_properties).issubset(new_properties):
        return False
    if not new_required.issubset(old_required):
        return False
    return all(
        old_properties[field].get("type") == new_properties[field].get("type")
        for field in old_properties
    )


def _missing_binding_findings(
    scan_id: str,
    trace_id: str | None,
    snapshot: ContractSnapshot,
    interfaces: dict[str, dict[str, Any]],
) -> list[InterfaceDriftFinding]:
    sdk_keys = set(interfaces)
    cli_keys = set(interfaces)
    policy_actions = {
        str(item.get("action"))
        for item in interfaces.values()
        if item.get("interface_type") == "policy_action" and item.get("action")
    }
    findings: list[InterfaceDriftFinding] = []
    for interface in interfaces.values():
        if interface.get("interface_type") not in {"api_route", "health_check"}:
            continue
        descriptor = _descriptor(interface)
        path = str(interface.get("path") or descriptor.get("path") or "")
        method = str(interface.get("method") or descriptor.get("method") or "GET")
        route_key = str(interface.get("interface_key") or f"{method} {path}")
        expect_sdk = bool(descriptor.get("expect_sdk")) or path.startswith("/brain/contracts")
        expect_cli = bool(descriptor.get("expect_cli")) or path.startswith("/brain/contracts")
        expected_policy = descriptor.get("expected_policy_action")
        if expect_sdk and not _has_binding(sdk_keys, path, "sdk"):
            findings.append(
                _binding_finding(scan_id, trace_id, "missing_sdk_binding", route_key, snapshot)
            )
        if expect_cli and not _has_binding(cli_keys, path, "cli"):
            findings.append(
                _binding_finding(scan_id, trace_id, "missing_cli_binding", route_key, snapshot)
            )
        if isinstance(expected_policy, str) and expected_policy not in policy_actions:
            findings.append(
                _finding(
                    scan_id,
                    trace_id,
                    "missing_policy_action",
                    "api_route",
                    None,
                    route_key,
                    "fastapi",
                    "high",
                    True,
                    f"Missing policy action for {route_key}",
                    f"Route {route_key} expects policy action {expected_policy}.",
                    "Add the generic policy action to the policy catalog and OPA policy.",
                )
            )
    return findings


def _payload_safety_findings(
    scan_id: str,
    trace_id: str | None,
    snapshot: ContractSnapshot,
) -> list[InterfaceDriftFinding]:
    findings: list[InterfaceDriftFinding] = []
    for kind in ("contracts", "interfaces"):
        for item in _manifest_items(snapshot, kind):
            key = str(item.get("contract_key") or item.get("interface_key") or "unknown")
            if _contains_secret_key(item):
                findings.append(
                    _finding(
                        scan_id,
                        trace_id,
                        "secret_leak",
                        str(item.get("interface_type") or item.get("contract_type") or "generic"),
                        item.get("contract_key"),
                        item.get("interface_key"),
                        str(item.get("source_system") or "contract_registry"),
                        "critical",
                        True,
                        f"Secret-like schema key in {key}",
                        f"{key} contains a secret-like key and must not be snapshotted.",
                        "Redact the schema descriptor before indexing it.",
                    )
                )
            if contains_disallowed_domain_term(key):
                findings.append(
                    _finding(
                        scan_id,
                        trace_id,
                        "domain_drift",
                        str(item.get("interface_type") or item.get("contract_type") or "generic"),
                        item.get("contract_key"),
                        item.get("interface_key"),
                        str(item.get("source_system") or "contract_registry"),
                        "high",
                        True,
                        f"Domain-specific interface {key}",
                        f"{key} contains domain-specific vocabulary outside Brain core.",
                        "Move domain-specific contracts outside Brain core.",
                    )
                )
    return findings


def _finding(
    scan_id: str,
    trace_id: str | None,
    finding_type: str,
    interface_type: str,
    contract_key: str | None,
    interface_key: str | None,
    source_system: str,
    severity: str,
    breaking: bool,
    title: str,
    description: str,
    recommended_action: str,
    *,
    old_ref: str | None = None,
    new_ref: str | None = None,
) -> InterfaceDriftFinding:
    return InterfaceDriftFinding(
        drift_finding_id=f"drift-finding-{uuid4().hex}",
        trace_id=trace_id,
        compatibility_scan_id=scan_id,
        finding_type=finding_type,  # type: ignore[arg-type]
        interface_type=interface_type,
        contract_key=contract_key,
        interface_key=interface_key,
        source_system=source_system,
        severity=severity,  # type: ignore[arg-type]
        status="open",
        breaking=breaking,
        title=title,
        description=description,
        old_ref=old_ref,
        new_ref=new_ref,
        recommended_action=recommended_action,
        metadata={"source_mutated": False},
        created_at=datetime.now(UTC),
    )


def _binding_finding(
    scan_id: str,
    trace_id: str | None,
    finding_type: str,
    route_key: str,
    snapshot: ContractSnapshot,
) -> InterfaceDriftFinding:
    action = "Add SDK binding." if finding_type == "missing_sdk_binding" else "Add CLI command."
    return _finding(
        scan_id,
        trace_id,
        finding_type,
        "api_route",
        None,
        route_key,
        "fastapi",
        "medium",
        False,
        f"{finding_type.replace('_', ' ').title()} for {route_key}",
        f"Route {route_key} is expected to have a matching binding.",
        action,
        new_ref=snapshot.contract_snapshot_id,
    )


def _removed_interface_kind(old: dict[str, Any]) -> tuple[str, str, bool, str]:
    interface_type = old.get("interface_type")
    if interface_type == "api_route":
        return ("removed_route", "high", True, "Restore the route or publish a migration path.")
    if interface_type == "sdk_method":
        return ("removed_sdk_method", "high", True, "Restore the SDK method or bump compatibility.")
    if interface_type == "cli_command":
        breaking = old.get("visibility") == "public"
        return (
            "removed_cli_command",
            "medium",
            breaking,
            "Restore the CLI command or document it.",
        )
    if interface_type == "policy_action":
        return ("removed_policy_action", "high", True, "Restore the policy action.")
    if interface_type == "env_setting":
        return ("removed_setting", "high", True, "Restore the setting or provide migration docs.")
    if interface_type == "telemetry_event":
        return ("removed_telemetry_event", "medium", True, "Restore the telemetry event.")
    return ("generic", "medium", False, "Review removed interface.")


def _manifest_items(snapshot: ContractSnapshot, key: str) -> list[dict[str, Any]]:
    value = snapshot.manifest.get(key, [])
    return [dict(item) for item in value if isinstance(item, dict)]


def _by_key(items: list[dict[str, Any]], key: str) -> dict[str, dict[str, Any]]:
    return {str(item[key]): item for item in items if item.get(key)}


def _schema(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("schema")
    return dict(value) if isinstance(value, dict) else {}


def _descriptor(item: dict[str, Any]) -> dict[str, Any]:
    value = item.get("descriptor")
    return dict(value) if isinstance(value, dict) else {}


def _required_fields(schema: dict[str, Any]) -> list[str]:
    required = schema.get("required", [])
    return [str(item) for item in required] if isinstance(required, list) else []


def _properties(schema: dict[str, Any]) -> dict[str, dict[str, Any]]:
    props = schema.get("properties", {})
    if not isinstance(props, dict):
        return {}
    return {str(key): dict(value) for key, value in props.items() if isinstance(value, dict)}


def _has_binding(keys: set[str], path: str, binding: str) -> bool:
    normalized = path.strip("/").replace("/", ".").replace("-", "_")
    return any(key.startswith(binding) and normalized in key.replace("-", "_") for key in keys)


def _contains_secret_key(value: Any) -> bool:
    blocked = ("api_key", "apikey", "authorization", "password", "private_key", "secret", "token")
    if isinstance(value, dict):
        for key, nested in value.items():
            normalized = str(key).lower().replace("-", "_")
            if any(part in normalized for part in blocked):
                return True
            if _contains_secret_key(nested):
                return True
    if isinstance(value, list):
        return any(_contains_secret_key(item) for item in value)
    return False


def _status(
    mode: str, breaking_count: int, warning_count: int
) -> CompatibilityScanStatus:
    if mode == "dry_run":
        return "dry_run"
    if breaking_count:
        return "failed"
    if warning_count:
        return "warning"
    return "passed"


def _blocked_scan(
    request: CompatibilityScanRequest,
    actor_context: ActorContext,
) -> CompatibilityScan:
    return CompatibilityScan(
        compatibility_scan_id=request.compatibility_scan_id or f"compatibility-scan-{uuid4().hex}",
        trace_id=request.trace_id or actor_context.trace_id,
        actor_id=request.actor_id or actor_context.actor_id,
        workspace_id=request.workspace_id or actor_context.workspace_id,
        status="blocked_by_policy",
        mode=request.mode,
        owner_scope=request.owner_scope,
        scan_scope=request.scan_scope,
        rules_applied=[],
        findings_count=0,
        breaking_count=0,
        warning_count=0,
        passed_count=0,
        findings=[],
        result={"blocked_by_policy": True},
        metadata=request.metadata,
        created_by=request.created_by or actor_context.actor_id,
        created_at=datetime.now(UTC),
        completed_at=datetime.now(UTC),
    )


def _publish_notification(notification_router: object | None, scan: CompatibilityScan) -> None:
    publish = getattr(notification_router, "publish", None) or getattr(
        notification_router, "route", None
    )
    if callable(publish):
        try:
            publish(
                {
                    "event_type": "compatibility_scan_completed",
                    "compatibility_scan_id": scan.compatibility_scan_id,
                    "breaking_count": scan.breaking_count,
                    "warning_count": scan.warning_count,
                }
            )
        except Exception:
            return


def _record_audit(audit_sink: object | None, event_type: str, resource_id: str) -> None:
    record = getattr(audit_sink, "record", None) or getattr(audit_sink, "record_event", None)
    if callable(record):
        try:
            record(event_type=event_type, resource_id=resource_id)
        except Exception:
            return


def _record_provenance(
    provenance_service: object | None,
    scan_id: str,
    snapshot_ids: list[str],
) -> None:
    record = getattr(provenance_service, "record", None) or getattr(
        provenance_service, "link", None
    )
    if callable(record):
        try:
            record(source_type="compatibility_scan", source_id=scan_id, target_refs=snapshot_ids)
        except Exception:
            return


__all__ = ["CompatibilityScanner"]
