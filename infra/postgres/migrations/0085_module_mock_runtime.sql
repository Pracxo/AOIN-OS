CREATE TABLE IF NOT EXISTS aion_module_mock_profiles (
    mock_profile_id TEXT PRIMARY KEY,
    profile_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    profile_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    supported_capability_types JSONB NOT NULL DEFAULT '[]'::jsonb,
    supported_capability_keys JSONB NOT NULL DEFAULT '[]'::jsonb,
    input_schema_hints JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_schema_hints JSONB NOT NULL DEFAULT '{}'::jsonb,
    simulation_rules JSONB NOT NULL DEFAULT '[]'::jsonb,
    constraints JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_module_mock_profiles_key
    ON aion_module_mock_profiles (profile_key);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_profiles_status
    ON aion_module_mock_profiles (status);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_profiles_type
    ON aion_module_mock_profiles (profile_type);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_profiles_created
    ON aion_module_mock_profiles (created_at);

CREATE TABLE IF NOT EXISTS aion_module_mock_invocation_requests (
    mock_invocation_request_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    mock_profile_id TEXT NULL,
    extension_package_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NOT NULL,
    capability_key TEXT NOT NULL,
    invocation_type TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    input_payload_hash TEXT NOT NULL,
    redacted_input_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    expected_output_shape JSONB NOT NULL DEFAULT '{}'::jsonb,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    policy_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    sandbox_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_trace
    ON aion_module_mock_invocation_requests (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_actor
    ON aion_module_mock_invocation_requests (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_workspace
    ON aion_module_mock_invocation_requests (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_profile
    ON aion_module_mock_invocation_requests (mock_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_extension
    ON aion_module_mock_invocation_requests (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_slot
    ON aion_module_mock_invocation_requests (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_binding
    ON aion_module_mock_invocation_requests (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_key
    ON aion_module_mock_invocation_requests (capability_key);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_type
    ON aion_module_mock_invocation_requests (invocation_type);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_mode
    ON aion_module_mock_invocation_requests (mode);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_requests_created
    ON aion_module_mock_invocation_requests (created_at);

CREATE TABLE IF NOT EXISTS aion_module_mock_runs (
    module_mock_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    mock_invocation_request_id TEXT NOT NULL,
    mock_profile_id TEXT NULL,
    extension_package_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NOT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    checks_run JSONB NOT NULL DEFAULT '[]'::jsonb,
    output_id TEXT NULL,
    finding_ids JSONB NOT NULL DEFAULT '[]'::jsonb,
    score DOUBLE PRECISION NOT NULL,
    schema_valid BOOLEAN NOT NULL DEFAULT false,
    policy_valid BOOLEAN NOT NULL DEFAULT false,
    sandbox_valid BOOLEAN NOT NULL DEFAULT false,
    activation_allowed BOOLEAN NOT NULL DEFAULT false,
    execution_allowed BOOLEAN NOT NULL DEFAULT false,
    external_calls_made BOOLEAN NOT NULL DEFAULT false,
    code_loaded BOOLEAN NOT NULL DEFAULT false,
    warnings JSONB NOT NULL DEFAULT '[]'::jsonb,
    failures JSONB NOT NULL DEFAULT '[]'::jsonb,
    result JSONB NOT NULL DEFAULT '{}'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_trace
    ON aion_module_mock_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_request
    ON aion_module_mock_runs (mock_invocation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_profile
    ON aion_module_mock_runs (mock_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_slot
    ON aion_module_mock_runs (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_binding
    ON aion_module_mock_runs (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_status
    ON aion_module_mock_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_mode
    ON aion_module_mock_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_score
    ON aion_module_mock_runs (score);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_schema
    ON aion_module_mock_runs (schema_valid);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_activation
    ON aion_module_mock_runs (activation_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_execution
    ON aion_module_mock_runs (execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_external
    ON aion_module_mock_runs (external_calls_made);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_code
    ON aion_module_mock_runs (code_loaded);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_runs_created
    ON aion_module_mock_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_module_mock_outputs (
    module_mock_output_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_mock_run_id TEXT NOT NULL,
    capability_binding_id TEXT NOT NULL,
    capability_key TEXT NOT NULL,
    output_type TEXT NOT NULL,
    status TEXT NOT NULL,
    output_payload_hash TEXT NOT NULL,
    redacted_output_payload JSONB NOT NULL DEFAULT '{}'::jsonb,
    output_summary TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    evidence_refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_trace
    ON aion_module_mock_outputs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_run
    ON aion_module_mock_outputs (module_mock_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_binding
    ON aion_module_mock_outputs (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_key
    ON aion_module_mock_outputs (capability_key);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_type
    ON aion_module_mock_outputs (output_type);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_status
    ON aion_module_mock_outputs (status);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_confidence
    ON aion_module_mock_outputs (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_outputs_created
    ON aion_module_mock_outputs (created_at);

CREATE TABLE IF NOT EXISTS aion_module_mock_findings (
    module_mock_finding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_mock_run_id TEXT NULL,
    mock_invocation_request_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    refs JSONB NOT NULL DEFAULT '[]'::jsonb,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_trace
    ON aion_module_mock_findings (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_run
    ON aion_module_mock_findings (module_mock_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_request
    ON aion_module_mock_findings (mock_invocation_request_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_slot
    ON aion_module_mock_findings (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_binding
    ON aion_module_mock_findings (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_type
    ON aion_module_mock_findings (finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_severity
    ON aion_module_mock_findings (severity);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_status
    ON aion_module_mock_findings (status);
CREATE INDEX IF NOT EXISTS ix_aion_module_mock_findings_created
    ON aion_module_mock_findings (created_at);
