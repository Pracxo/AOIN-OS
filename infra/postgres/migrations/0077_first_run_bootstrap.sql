CREATE TABLE IF NOT EXISTS aion_bootstrap_profiles (
    bootstrap_profile_id TEXT PRIMARY KEY,
    profile_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    profile_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    required_services JSONB NOT NULL,
    required_settings JSONB NOT NULL,
    seed_bundle_keys JSONB NOT NULL,
    checks JSONB NOT NULL,
    constraints JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_profiles_key ON aion_bootstrap_profiles(profile_key);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_profiles_status ON aion_bootstrap_profiles(status);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_profiles_type ON aion_bootstrap_profiles(profile_type);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_profiles_created_at ON aion_bootstrap_profiles(created_at);

CREATE TABLE IF NOT EXISTS aion_seed_bundles (
    seed_bundle_id TEXT PRIMARY KEY,
    seed_bundle_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    bundle_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    seed_steps JSONB NOT NULL,
    idempotency_keys JSONB NOT NULL,
    dependencies JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_seed_bundles_key ON aion_seed_bundles(seed_bundle_key);
CREATE INDEX IF NOT EXISTS ix_aion_seed_bundles_status ON aion_seed_bundles(status);
CREATE INDEX IF NOT EXISTS ix_aion_seed_bundles_type ON aion_seed_bundles(bundle_type);
CREATE INDEX IF NOT EXISTS ix_aion_seed_bundles_created_at ON aion_seed_bundles(created_at);

CREATE TABLE IF NOT EXISTS aion_seed_execution_records (
    seed_execution_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    seed_bundle_id TEXT NOT NULL,
    seed_bundle_key TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    steps_attempted INTEGER NOT NULL,
    steps_completed INTEGER NOT NULL,
    steps_skipped INTEGER NOT NULL,
    steps_failed INTEGER NOT NULL,
    created_resource_refs JSONB NOT NULL,
    skipped_resource_refs JSONB NOT NULL,
    failures JSONB NOT NULL,
    warnings JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_trace ON aion_seed_execution_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_actor ON aion_seed_execution_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_workspace ON aion_seed_execution_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_bundle_id ON aion_seed_execution_records(seed_bundle_id);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_bundle_key ON aion_seed_execution_records(seed_bundle_key);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_status ON aion_seed_execution_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_mode ON aion_seed_execution_records(mode);
CREATE INDEX IF NOT EXISTS ix_aion_seed_execution_created_at ON aion_seed_execution_records(created_at);

CREATE TABLE IF NOT EXISTS aion_setup_findings (
    setup_finding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    finding_type TEXT NOT NULL,
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    check_key TEXT NOT NULL,
    expected JSONB NOT NULL,
    actual JSONB NOT NULL,
    recommended_action TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_trace ON aion_setup_findings(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_type ON aion_setup_findings(finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_category ON aion_setup_findings(category);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_severity ON aion_setup_findings(severity);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_status ON aion_setup_findings(status);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_check_key ON aion_setup_findings(check_key);
CREATE INDEX IF NOT EXISTS ix_aion_setup_findings_created_at ON aion_setup_findings(created_at);

CREATE TABLE IF NOT EXISTS aion_bootstrap_runs (
    bootstrap_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    bootstrap_profile_id TEXT NULL,
    profile_key TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    checks_run JSONB NOT NULL,
    seed_execution_ids JSONB NOT NULL,
    setup_finding_ids JSONB NOT NULL,
    golden_path_run_id TEXT NULL,
    release_smoke_ref TEXT NULL,
    readiness_score DOUBLE PRECISION NOT NULL,
    local_ready BOOLEAN NOT NULL,
    warnings JSONB NOT NULL,
    failures JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_trace ON aion_bootstrap_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_actor ON aion_bootstrap_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_workspace ON aion_bootstrap_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_profile_id ON aion_bootstrap_runs(bootstrap_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_profile_key ON aion_bootstrap_runs(profile_key);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_status ON aion_bootstrap_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_mode ON aion_bootstrap_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_score ON aion_bootstrap_runs(readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_local_ready ON aion_bootstrap_runs(local_ready);
CREATE INDEX IF NOT EXISTS ix_aion_bootstrap_runs_created_at ON aion_bootstrap_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_setup_reports (
    setup_report_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    bootstrap_run_id TEXT NULL,
    readiness_score DOUBLE PRECISION NOT NULL,
    local_ready BOOLEAN NOT NULL,
    health_ready BOOLEAN NOT NULL,
    policy_ready BOOLEAN NOT NULL,
    sdk_ready BOOLEAN NOT NULL,
    cli_ready BOOLEAN NOT NULL,
    golden_path_ready BOOLEAN NOT NULL,
    release_smoke_ready BOOLEAN NOT NULL,
    docker_ready BOOLEAN NOT NULL,
    finding_count INTEGER NOT NULL,
    critical_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    report JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_trace ON aion_setup_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_status ON aion_setup_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_bootstrap_run ON aion_setup_reports(bootstrap_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_score ON aion_setup_reports(readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_local_ready ON aion_setup_reports(local_ready);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_critical ON aion_setup_reports(critical_count);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_warning ON aion_setup_reports(warning_count);
CREATE INDEX IF NOT EXISTS ix_aion_setup_reports_created_at ON aion_setup_reports(created_at);
