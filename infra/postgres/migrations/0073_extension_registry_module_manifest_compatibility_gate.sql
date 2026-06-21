CREATE TABLE IF NOT EXISTS aion_extension_packages (
    extension_package_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    extension_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    package_type TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_ref TEXT NULL,
    owner_scope JSONB NOT NULL,
    manifest_hash TEXT NOT NULL,
    manifest JSONB NOT NULL,
    declared_capabilities JSONB NOT NULL,
    declared_contracts JSONB NOT NULL,
    declared_dependencies JSONB NOT NULL,
    declared_policy_actions JSONB NOT NULL,
    declared_settings JSONB NOT NULL,
    declared_routes JSONB NOT NULL,
    declared_events JSONB NOT NULL,
    declared_resources JSONB NOT NULL,
    compatibility_status TEXT NOT NULL,
    review_status TEXT NOT NULL,
    install_plan_id TEXT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_aion_extension_packages_key_version_active
    ON aion_extension_packages (extension_key, version)
    WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_extension_key ON aion_extension_packages (extension_key);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_name ON aion_extension_packages (name);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_version ON aion_extension_packages (version);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_status ON aion_extension_packages (status);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_package_type ON aion_extension_packages (package_type);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_source_type ON aion_extension_packages (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_manifest_hash ON aion_extension_packages (manifest_hash);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_compatibility_status ON aion_extension_packages (compatibility_status);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_review_status ON aion_extension_packages (review_status);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_created_at ON aion_extension_packages (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_extension_packages_deleted_at ON aion_extension_packages (deleted_at);

CREATE TABLE IF NOT EXISTS aion_extension_capability_declarations (
    capability_declaration_id TEXT PRIMARY KEY,
    extension_package_id TEXT NOT NULL REFERENCES aion_extension_packages(extension_package_id),
    capability_key TEXT NOT NULL,
    capability_type TEXT NOT NULL,
    status TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    requires_policy BOOLEAN NOT NULL,
    requires_approval BOOLEAN NOT NULL,
    requires_sandbox BOOLEAN NOT NULL,
    dry_run_supported BOOLEAN NOT NULL,
    controlled_supported BOOLEAN NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    constraints JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_package ON aion_extension_capability_declarations (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_key ON aion_extension_capability_declarations (capability_key);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_type ON aion_extension_capability_declarations (capability_type);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_status ON aion_extension_capability_declarations (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_risk ON aion_extension_capability_declarations (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_requires_policy ON aion_extension_capability_declarations (requires_policy);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_requires_approval ON aion_extension_capability_declarations (requires_approval);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_requires_sandbox ON aion_extension_capability_declarations (requires_sandbox);
CREATE INDEX IF NOT EXISTS ix_aion_ext_cap_created_at ON aion_extension_capability_declarations (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_dependency_declarations (
    dependency_declaration_id TEXT PRIMARY KEY,
    extension_package_id TEXT NOT NULL REFERENCES aion_extension_packages(extension_package_id),
    dependency_key TEXT NOT NULL,
    dependency_type TEXT NOT NULL,
    version_constraint TEXT NULL,
    required BOOLEAN NOT NULL,
    status TEXT NOT NULL,
    source TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_package ON aion_extension_dependency_declarations (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_key ON aion_extension_dependency_declarations (dependency_key);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_type ON aion_extension_dependency_declarations (dependency_type);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_required ON aion_extension_dependency_declarations (required);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_status ON aion_extension_dependency_declarations (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_source ON aion_extension_dependency_declarations (source);
CREATE INDEX IF NOT EXISTS ix_aion_ext_dep_created_at ON aion_extension_dependency_declarations (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_compatibility_runs (
    extension_compatibility_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    extension_package_id TEXT NOT NULL REFERENCES aion_extension_packages(extension_package_id),
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    contract_snapshot_id TEXT NULL,
    compatibility_scan_id TEXT NULL,
    checks JSONB NOT NULL,
    findings JSONB NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_trace ON aion_extension_compatibility_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_package ON aion_extension_compatibility_runs (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_status ON aion_extension_compatibility_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_mode ON aion_extension_compatibility_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_snapshot ON aion_extension_compatibility_runs (contract_snapshot_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_scan ON aion_extension_compatibility_runs (compatibility_scan_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_score ON aion_extension_compatibility_runs (score);
CREATE INDEX IF NOT EXISTS ix_aion_ext_compat_created_at ON aion_extension_compatibility_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_intake_runs (
    extension_intake_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    extension_package JSONB NULL,
    extension_package_id TEXT NULL,
    manifest_hash TEXT NOT NULL,
    validation_status TEXT NOT NULL,
    compatibility_status TEXT NOT NULL,
    review_required BOOLEAN NOT NULL,
    install_plan_created BOOLEAN NOT NULL,
    findings JSONB NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_trace ON aion_extension_intake_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_actor ON aion_extension_intake_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_workspace ON aion_extension_intake_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_status ON aion_extension_intake_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_mode ON aion_extension_intake_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_package ON aion_extension_intake_runs (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_manifest_hash ON aion_extension_intake_runs (manifest_hash);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_validation ON aion_extension_intake_runs (validation_status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_compat ON aion_extension_intake_runs (compatibility_status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_review ON aion_extension_intake_runs (review_required);
CREATE INDEX IF NOT EXISTS ix_aion_ext_intake_created_at ON aion_extension_intake_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_reviews (
    extension_review_id TEXT PRIMARY KEY,
    extension_package_id TEXT NOT NULL REFERENCES aion_extension_packages(extension_package_id),
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer_id TEXT NULL,
    reason TEXT NOT NULL,
    approval_request_id TEXT NULL,
    policy_decision_id TEXT NULL,
    blocker_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_package ON aion_extension_reviews (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_trace ON aion_extension_reviews (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_actor ON aion_extension_reviews (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_workspace ON aion_extension_reviews (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_status ON aion_extension_reviews (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_decision ON aion_extension_reviews (decision);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_reviewer ON aion_extension_reviews (reviewer_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_approval ON aion_extension_reviews (approval_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_reviews_created_at ON aion_extension_reviews (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_install_plans (
    install_plan_id TEXT PRIMARY KEY,
    extension_package_id TEXT NOT NULL REFERENCES aion_extension_packages(extension_package_id),
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    steps JSONB NOT NULL,
    required_approvals JSONB NOT NULL,
    required_settings JSONB NOT NULL,
    required_policy_actions JSONB NOT NULL,
    required_contracts JSONB NOT NULL,
    required_sandbox_profiles JSONB NOT NULL,
    blocked BOOLEAN NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    executable BOOLEAN NOT NULL DEFAULT false,
    execution_allowed BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_package ON aion_extension_install_plans (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_trace ON aion_extension_install_plans (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_status ON aion_extension_install_plans (status);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_type ON aion_extension_install_plans (plan_type);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_blocked ON aion_extension_install_plans (blocked);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_executable ON aion_extension_install_plans (executable);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_execution_allowed ON aion_extension_install_plans (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_ext_plans_created_at ON aion_extension_install_plans (created_at);
