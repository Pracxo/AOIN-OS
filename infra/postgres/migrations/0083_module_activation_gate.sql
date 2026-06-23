CREATE TABLE IF NOT EXISTS aion_module_activation_requests (
    activation_request_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    extension_package_id TEXT NULL,
    module_slot_id TEXT NOT NULL,
    capability_binding_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    readiness_assessment_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    conformance_run_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    status TEXT NOT NULL,
    request_type TEXT NOT NULL,
    activation_target TEXT NOT NULL,
    requested_mode TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_approvals JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_policy_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_settings JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_sandbox_profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocker_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    activation_plan_id TEXT NULL,
    registration_preview_id TEXT NULL,
    rollback_plan_id TEXT NULL,
    activation_allowed BOOLEAN NOT NULL DEFAULT false,
    execution_allowed BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    reviewed_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_trace
    ON aion_module_activation_requests (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_actor
    ON aion_module_activation_requests (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_workspace
    ON aion_module_activation_requests (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_extension
    ON aion_module_activation_requests (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_slot
    ON aion_module_activation_requests (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_status
    ON aion_module_activation_requests (status);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_type
    ON aion_module_activation_requests (request_type);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_target
    ON aion_module_activation_requests (activation_target);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_mode
    ON aion_module_activation_requests (requested_mode);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_risk
    ON aion_module_activation_requests (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_created
    ON aion_module_activation_requests (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_activation_requests_deleted
    ON aion_module_activation_requests (deleted_at);

CREATE TABLE IF NOT EXISTS aion_module_activation_blockers (
    activation_blocker_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    activation_request_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    blocker_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    missing_requirement TEXT NULL,
    source_type TEXT NULL,
    source_id TEXT NULL,
    recommended_action TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_request
    ON aion_module_activation_blockers (activation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_slot
    ON aion_module_activation_blockers (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_binding
    ON aion_module_activation_blockers (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_type
    ON aion_module_activation_blockers (blocker_type);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_severity
    ON aion_module_activation_blockers (severity);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_status
    ON aion_module_activation_blockers (status);
CREATE INDEX IF NOT EXISTS ix_aion_activation_blockers_created
    ON aion_module_activation_blockers (created_at);

CREATE TABLE IF NOT EXISTS aion_module_activation_gate_runs (
    activation_gate_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    activation_request_id TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    checks_run JSONB NOT NULL DEFAULT '[]'::jsonb,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    score DOUBLE PRECISION NOT NULL,
    activation_allowed BOOLEAN NOT NULL DEFAULT false,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_activation_gate_runs_trace
    ON aion_module_activation_gate_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_gate_runs_request
    ON aion_module_activation_gate_runs (activation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_gate_runs_status
    ON aion_module_activation_gate_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_activation_gate_runs_mode
    ON aion_module_activation_gate_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_activation_gate_runs_created
    ON aion_module_activation_gate_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_module_activation_reviews (
    activation_review_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    activation_request_id TEXT NOT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    decision TEXT NOT NULL,
    reviewer_id TEXT NULL,
    reason TEXT NOT NULL,
    approval_request_id TEXT NULL,
    policy_decision_id TEXT NULL,
    blocker_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_activation_reviews_request
    ON aion_module_activation_reviews (activation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_reviews_decision
    ON aion_module_activation_reviews (decision);
CREATE INDEX IF NOT EXISTS ix_aion_activation_reviews_created
    ON aion_module_activation_reviews (created_at);

CREATE TABLE IF NOT EXISTS aion_module_activation_plans (
    activation_plan_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    activation_request_id TEXT NOT NULL,
    module_slot_id TEXT NOT NULL,
    status TEXT NOT NULL,
    plan_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    steps JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_contracts JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_policy_actions JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_settings JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_sandbox_profiles JSONB NOT NULL DEFAULT '[]'::jsonb,
    required_approvals JSONB NOT NULL DEFAULT '[]'::jsonb,
    rollback_plan JSONB NOT NULL DEFAULT '[]'::jsonb,
    blocked BOOLEAN NOT NULL DEFAULT true,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    executable BOOLEAN NOT NULL DEFAULT false,
    execution_allowed BOOLEAN NOT NULL DEFAULT false,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_activation_plans_request
    ON aion_module_activation_plans (activation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_plans_slot
    ON aion_module_activation_plans (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_activation_plans_status
    ON aion_module_activation_plans (status);
CREATE INDEX IF NOT EXISTS ix_aion_activation_plans_created
    ON aion_module_activation_plans (created_at);

CREATE TABLE IF NOT EXISTS aion_runtime_registration_previews (
    registration_preview_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    activation_request_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    status TEXT NOT NULL,
    preview_type TEXT NOT NULL,
    target_runtime TEXT NOT NULL,
    target_ref TEXT NULL,
    route_previews JSONB NOT NULL DEFAULT '[]'::jsonb,
    capability_previews JSONB NOT NULL DEFAULT '[]'::jsonb,
    policy_action_previews JSONB NOT NULL DEFAULT '[]'::jsonb,
    setting_previews JSONB NOT NULL DEFAULT '[]'::jsonb,
    would_register BOOLEAN NOT NULL DEFAULT false,
    registration_allowed BOOLEAN NOT NULL DEFAULT false,
    blockers JSONB NOT NULL DEFAULT '[]'::jsonb,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_runtime_registration_previews_request
    ON aion_runtime_registration_previews (activation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_runtime_registration_previews_slot
    ON aion_runtime_registration_previews (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_runtime_registration_previews_binding
    ON aion_runtime_registration_previews (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_runtime_registration_previews_status
    ON aion_runtime_registration_previews (status);
CREATE INDEX IF NOT EXISTS ix_aion_runtime_registration_previews_created
    ON aion_runtime_registration_previews (created_at);
