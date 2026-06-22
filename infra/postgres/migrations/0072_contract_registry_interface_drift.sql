CREATE TABLE IF NOT EXISTS aion_contract_index_records (
    contract_index_id TEXT PRIMARY KEY,
    contract_key TEXT NOT NULL,
    contract_type TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_symbol TEXT NOT NULL,
    status TEXT NOT NULL,
    visibility TEXT NOT NULL,
    version TEXT NOT NULL,
    schema_hash TEXT NOT NULL,
    schema JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    tags JSONB NOT NULL,
    metadata JSONB NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deprecated_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_aion_contract_index_key_version_active
    ON aion_contract_index_records(contract_key, version)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_contract_key ON aion_contract_index_records(contract_key);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_contract_type ON aion_contract_index_records(contract_type);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_source_path ON aion_contract_index_records(source_path);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_source_symbol ON aion_contract_index_records(source_symbol);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_status ON aion_contract_index_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_visibility ON aion_contract_index_records(visibility);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_version ON aion_contract_index_records(version);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_schema_hash ON aion_contract_index_records(schema_hash);
CREATE INDEX IF NOT EXISTS ix_aion_contract_index_deleted_at ON aion_contract_index_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_interface_inventory_records (
    interface_id TEXT PRIMARY KEY,
    interface_key TEXT NOT NULL,
    interface_type TEXT NOT NULL,
    source_system TEXT NOT NULL,
    status TEXT NOT NULL,
    visibility TEXT NOT NULL,
    version TEXT NOT NULL,
    path TEXT NULL,
    method TEXT NULL,
    command TEXT NULL,
    action TEXT NULL,
    setting_key TEXT NULL,
    feature_key TEXT NULL,
    telemetry_key TEXT NULL,
    resource_type TEXT NULL,
    schema_hash TEXT NOT NULL,
    descriptor JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    first_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deprecated_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_aion_interface_inventory_key_version_active
    ON aion_interface_inventory_records(interface_key, version)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_interface_key ON aion_interface_inventory_records(interface_key);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_interface_type ON aion_interface_inventory_records(interface_type);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_source_system ON aion_interface_inventory_records(source_system);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_status ON aion_interface_inventory_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_visibility ON aion_interface_inventory_records(visibility);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_version ON aion_interface_inventory_records(version);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_path ON aion_interface_inventory_records(path);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_method ON aion_interface_inventory_records(method);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_command ON aion_interface_inventory_records(command);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_action ON aion_interface_inventory_records(action);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_setting_key ON aion_interface_inventory_records(setting_key);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_feature_key ON aion_interface_inventory_records(feature_key);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_telemetry_key ON aion_interface_inventory_records(telemetry_key);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_resource_type ON aion_interface_inventory_records(resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_schema_hash ON aion_interface_inventory_records(schema_hash);
CREATE INDEX IF NOT EXISTS ix_aion_interface_inventory_deleted_at ON aion_interface_inventory_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_contract_snapshots (
    contract_snapshot_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    snapshot_type TEXT NOT NULL,
    status TEXT NOT NULL,
    version TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    contract_count INTEGER NOT NULL,
    interface_count INTEGER NOT NULL,
    policy_action_count INTEGER NOT NULL,
    route_count INTEGER NOT NULL,
    sdk_resource_count INTEGER NOT NULL,
    cli_command_count INTEGER NOT NULL,
    setting_count INTEGER NOT NULL,
    telemetry_count INTEGER NOT NULL,
    root_hash TEXT NOT NULL,
    manifest JSONB NOT NULL,
    report JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_trace ON aion_contract_snapshots(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_snapshot_type ON aion_contract_snapshots(snapshot_type);
CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_status ON aion_contract_snapshots(status);
CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_version ON aion_contract_snapshots(version);
CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_root_hash ON aion_contract_snapshots(root_hash);
CREATE INDEX IF NOT EXISTS ix_aion_contract_snapshots_created_at ON aion_contract_snapshots(created_at);

CREATE TABLE IF NOT EXISTS aion_compatibility_rules (
    compatibility_rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    applies_to JSONB NOT NULL,
    rule JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_compat_rules_name ON aion_compatibility_rules(name);
CREATE INDEX IF NOT EXISTS ix_aion_compat_rules_status ON aion_compatibility_rules(status);
CREATE INDEX IF NOT EXISTS ix_aion_compat_rules_rule_type ON aion_compatibility_rules(rule_type);
CREATE INDEX IF NOT EXISTS ix_aion_compat_rules_severity ON aion_compatibility_rules(severity);
CREATE INDEX IF NOT EXISTS ix_aion_compat_rules_created_at ON aion_compatibility_rules(created_at);

CREATE TABLE IF NOT EXISTS aion_interface_drift_findings (
    drift_finding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    compatibility_scan_id TEXT NULL,
    finding_type TEXT NOT NULL,
    interface_type TEXT NOT NULL,
    contract_key TEXT NULL,
    interface_key TEXT NULL,
    source_system TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    breaking BOOLEAN NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    old_ref TEXT NULL,
    new_ref TEXT NULL,
    recommended_action TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_trace ON aion_interface_drift_findings(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_scan ON aion_interface_drift_findings(compatibility_scan_id);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_finding_type ON aion_interface_drift_findings(finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_interface_type ON aion_interface_drift_findings(interface_type);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_contract_key ON aion_interface_drift_findings(contract_key);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_interface_key ON aion_interface_drift_findings(interface_key);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_source_system ON aion_interface_drift_findings(source_system);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_severity ON aion_interface_drift_findings(severity);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_status ON aion_interface_drift_findings(status);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_breaking ON aion_interface_drift_findings(breaking);
CREATE INDEX IF NOT EXISTS ix_aion_drift_findings_created_at ON aion_interface_drift_findings(created_at);

CREATE TABLE IF NOT EXISTS aion_compatibility_scans (
    compatibility_scan_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    baseline_snapshot_id TEXT NULL,
    candidate_snapshot_id TEXT NULL,
    scan_scope JSONB NOT NULL,
    rules_applied JSONB NOT NULL,
    findings_count INTEGER NOT NULL,
    breaking_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    passed_count INTEGER NOT NULL,
    findings JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_trace ON aion_compatibility_scans(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_actor ON aion_compatibility_scans(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_workspace ON aion_compatibility_scans(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_status ON aion_compatibility_scans(status);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_mode ON aion_compatibility_scans(mode);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_baseline ON aion_compatibility_scans(baseline_snapshot_id);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_candidate ON aion_compatibility_scans(candidate_snapshot_id);
CREATE INDEX IF NOT EXISTS ix_aion_compat_scans_created_at ON aion_compatibility_scans(created_at);

CREATE TABLE IF NOT EXISTS aion_migration_notes (
    migration_note_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    compatibility_scan_id TEXT NULL,
    finding_id TEXT NULL,
    note_type TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_contracts JSONB NOT NULL,
    affected_interfaces JSONB NOT NULL,
    migration_steps JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_trace ON aion_migration_notes(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_scan ON aion_migration_notes(compatibility_scan_id);
CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_finding ON aion_migration_notes(finding_id);
CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_note_type ON aion_migration_notes(note_type);
CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_status ON aion_migration_notes(status);
CREATE INDEX IF NOT EXISTS ix_aion_migration_notes_created_at ON aion_migration_notes(created_at);

CREATE TABLE IF NOT EXISTS aion_contract_registry_reports (
    contract_report_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    snapshot_id TEXT NULL,
    latest_scan_id TEXT NULL,
    contract_count INTEGER NOT NULL,
    interface_count INTEGER NOT NULL,
    active_breaking_findings INTEGER NOT NULL,
    active_warning_findings INTEGER NOT NULL,
    deprecated_count INTEGER NOT NULL,
    missing_sdk_count INTEGER NOT NULL,
    missing_cli_count INTEGER NOT NULL,
    missing_policy_count INTEGER NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_trace ON aion_contract_registry_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_status ON aion_contract_registry_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_snapshot ON aion_contract_registry_reports(snapshot_id);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_latest_scan ON aion_contract_registry_reports(latest_scan_id);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_breaking ON aion_contract_registry_reports(active_breaking_findings);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_warning ON aion_contract_registry_reports(active_warning_findings);
CREATE INDEX IF NOT EXISTS ix_aion_contract_reports_created_at ON aion_contract_registry_reports(created_at);
