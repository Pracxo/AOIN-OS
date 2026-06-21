CREATE TABLE IF NOT EXISTS aion_module_slots (
    module_slot_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    extension_package_id TEXT NULL,
    slot_key TEXT NOT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    slot_type TEXT NOT NULL,
    lifecycle_state TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    compatibility_status TEXT NOT NULL,
    allowed_modes JSONB NOT NULL,
    declared_capability_refs JSONB NOT NULL,
    capability_binding_refs JSONB NOT NULL,
    contract_refs JSONB NOT NULL,
    policy_action_refs JSONB NOT NULL,
    setting_refs JSONB NOT NULL,
    sandbox_profile_id TEXT NULL,
    mount_plan_id TEXT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_module_slots_extension_package ON aion_module_slots (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_slot_key ON aion_module_slots (slot_key);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_status ON aion_module_slots (status);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_type ON aion_module_slots (slot_type);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_lifecycle ON aion_module_slots (lifecycle_state);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_compat ON aion_module_slots (compatibility_status);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_sandbox ON aion_module_slots (sandbox_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_mount_plan ON aion_module_slots (mount_plan_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_created_at ON aion_module_slots (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_module_slots_deleted_at ON aion_module_slots (deleted_at);

CREATE TABLE IF NOT EXISTS aion_capability_bindings (
    capability_binding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NOT NULL,
    extension_package_id TEXT NULL,
    capability_key TEXT NOT NULL,
    capability_type TEXT NOT NULL,
    binding_type TEXT NOT NULL,
    status TEXT NOT NULL,
    route_key TEXT NULL,
    target_runtime TEXT NOT NULL,
    target_ref TEXT NULL,
    risk_level TEXT NOT NULL,
    allowed_modes JSONB NOT NULL,
    input_schema JSONB NOT NULL,
    output_schema JSONB NOT NULL,
    required_policy_actions JSONB NOT NULL,
    required_settings JSONB NOT NULL,
    required_contracts JSONB NOT NULL,
    requires_approval BOOLEAN NOT NULL,
    requires_sandbox BOOLEAN NOT NULL,
    sandbox_profile_id TEXT NULL,
    dry_run_supported BOOLEAN NOT NULL,
    controlled_supported BOOLEAN NOT NULL,
    constraints JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_slot ON aion_capability_bindings (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_extension_package ON aion_capability_bindings (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_key ON aion_capability_bindings (capability_key);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_type ON aion_capability_bindings (capability_type);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_binding_type ON aion_capability_bindings (binding_type);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_status ON aion_capability_bindings (status);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_runtime ON aion_capability_bindings (target_runtime);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_route ON aion_capability_bindings (route_key);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_risk ON aion_capability_bindings (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_approval ON aion_capability_bindings (requires_approval);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_sandbox ON aion_capability_bindings (requires_sandbox);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_sandbox_profile ON aion_capability_bindings (sandbox_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_created_at ON aion_capability_bindings (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_cap_bindings_deleted_at ON aion_capability_bindings (deleted_at);

CREATE TABLE IF NOT EXISTS aion_binding_validation_runs (
    binding_validation_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    module_slot_id TEXT NULL,
    extension_package_id TEXT NULL,
    capability_binding_ids JSONB NOT NULL,
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

CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_trace ON aion_binding_validation_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_actor ON aion_binding_validation_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_workspace ON aion_binding_validation_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_status ON aion_binding_validation_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_mode ON aion_binding_validation_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_slot ON aion_binding_validation_runs (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_extension_package ON aion_binding_validation_runs (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_score ON aion_binding_validation_runs (score);
CREATE INDEX IF NOT EXISTS ix_aion_binding_validations_created_at ON aion_binding_validation_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_module_mount_plans (
    mount_plan_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NOT NULL,
    extension_package_id TEXT NULL,
    status TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    steps JSONB NOT NULL,
    required_contracts JSONB NOT NULL,
    required_policy_actions JSONB NOT NULL,
    required_settings JSONB NOT NULL,
    required_sandbox_profiles JSONB NOT NULL,
    capability_binding_ids JSONB NOT NULL,
    blocked BOOLEAN NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    executable BOOLEAN NOT NULL,
    execution_allowed BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_slot ON aion_module_mount_plans (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_extension_package ON aion_module_mount_plans (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_status ON aion_module_mount_plans (status);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_type ON aion_module_mount_plans (plan_type);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_blocked ON aion_module_mount_plans (blocked);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_executable ON aion_module_mount_plans (executable);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_execution_allowed ON aion_module_mount_plans (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_mount_plans_created_at ON aion_module_mount_plans (created_at);

CREATE TABLE IF NOT EXISTS aion_route_binding_previews (
    route_preview_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    status TEXT NOT NULL,
    route_key TEXT NOT NULL,
    route_type TEXT NOT NULL,
    method TEXT NULL,
    path TEXT NULL,
    target_runtime TEXT NOT NULL,
    target_ref TEXT NULL,
    would_register BOOLEAN NOT NULL,
    registration_allowed BOOLEAN NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_route_previews_slot ON aion_route_binding_previews (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_binding ON aion_route_binding_previews (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_status ON aion_route_binding_previews (status);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_key ON aion_route_binding_previews (route_key);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_type ON aion_route_binding_previews (route_type);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_method ON aion_route_binding_previews (method);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_path ON aion_route_binding_previews (path);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_runtime ON aion_route_binding_previews (target_runtime);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_would_register ON aion_route_binding_previews (would_register);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_registration ON aion_route_binding_previews (registration_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_route_previews_created_at ON aion_route_binding_previews (created_at);

CREATE TABLE IF NOT EXISTS aion_binding_conflicts (
    binding_conflict_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    conflict_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    conflicting_refs JSONB NOT NULL,
    recommended_action TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_slot ON aion_binding_conflicts (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_binding ON aion_binding_conflicts (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_type ON aion_binding_conflicts (conflict_type);
CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_severity ON aion_binding_conflicts (severity);
CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_status ON aion_binding_conflicts (status);
CREATE INDEX IF NOT EXISTS ix_aion_binding_conflicts_created_at ON aion_binding_conflicts (created_at);
