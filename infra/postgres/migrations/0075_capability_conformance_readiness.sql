CREATE TABLE IF NOT EXISTS aion_conformance_profiles (
    conformance_profile_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    profile_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    required_checks JSONB NOT NULL,
    optional_checks JSONB NOT NULL,
    minimum_score DOUBLE PRECISION NOT NULL,
    fail_on_critical BOOLEAN NOT NULL,
    fail_on_missing_contract BOOLEAN NOT NULL,
    fail_on_missing_policy_action BOOLEAN NOT NULL,
    fail_on_missing_sandbox BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_conformance_profiles_name
    ON aion_conformance_profiles (name);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_profiles_status
    ON aion_conformance_profiles (status);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_profiles_type
    ON aion_conformance_profiles (profile_type);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_profiles_score
    ON aion_conformance_profiles (minimum_score);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_profiles_created_at
    ON aion_conformance_profiles (created_at);

CREATE TABLE IF NOT EXISTS aion_capability_test_vectors (
    test_vector_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    extension_package_id TEXT NULL,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    vector_type TEXT NOT NULL,
    input_payload JSONB NOT NULL,
    expected_output_shape JSONB NOT NULL,
    expected_constraints JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_slot
    ON aion_capability_test_vectors (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_binding
    ON aion_capability_test_vectors (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_extension
    ON aion_capability_test_vectors (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_status
    ON aion_capability_test_vectors (status);
CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_type
    ON aion_capability_test_vectors (vector_type);
CREATE INDEX IF NOT EXISTS ix_aion_test_vectors_created_at
    ON aion_capability_test_vectors (created_at);

CREATE TABLE IF NOT EXISTS aion_mock_invocation_records (
    mock_invocation_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    extension_package_id TEXT NULL,
    test_vector_id TEXT NULL,
    status TEXT NOT NULL,
    invocation_type TEXT NOT NULL,
    input_payload_hash TEXT NOT NULL,
    redacted_input_payload JSONB NOT NULL,
    simulated_output JSONB NOT NULL,
    schema_valid BOOLEAN NOT NULL,
    policy_valid BOOLEAN NOT NULL,
    sandbox_valid BOOLEAN NOT NULL,
    findings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_slot
    ON aion_mock_invocation_records (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_binding
    ON aion_mock_invocation_records (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_extension
    ON aion_mock_invocation_records (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_vector
    ON aion_mock_invocation_records (test_vector_id);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_status
    ON aion_mock_invocation_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_type
    ON aion_mock_invocation_records (invocation_type);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_schema
    ON aion_mock_invocation_records (schema_valid);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_policy
    ON aion_mock_invocation_records (policy_valid);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_sandbox
    ON aion_mock_invocation_records (sandbox_valid);
CREATE INDEX IF NOT EXISTS ix_aion_mock_invocations_created_at
    ON aion_mock_invocation_records (created_at);

CREATE TABLE IF NOT EXISTS aion_conformance_runs (
    conformance_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    conformance_profile_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    extension_package_id TEXT NULL,
    checks_run JSONB NOT NULL,
    test_vector_ids JSONB NOT NULL,
    mock_invocations JSONB NOT NULL,
    findings JSONB NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    passed BOOLEAN NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_trace
    ON aion_conformance_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_actor
    ON aion_conformance_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_workspace
    ON aion_conformance_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_status
    ON aion_conformance_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_mode
    ON aion_conformance_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_profile
    ON aion_conformance_runs (conformance_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_slot
    ON aion_conformance_runs (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_binding
    ON aion_conformance_runs (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_extension
    ON aion_conformance_runs (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_score
    ON aion_conformance_runs (score);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_passed
    ON aion_conformance_runs (passed);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_runs_created_at
    ON aion_conformance_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_conformance_findings (
    conformance_finding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    conformance_run_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    extension_package_id TEXT NULL,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_run
    ON aion_conformance_findings (conformance_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_slot
    ON aion_conformance_findings (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_binding
    ON aion_conformance_findings (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_extension
    ON aion_conformance_findings (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_type
    ON aion_conformance_findings (finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_severity
    ON aion_conformance_findings (severity);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_status
    ON aion_conformance_findings (status);
CREATE INDEX IF NOT EXISTS ix_aion_conformance_findings_created_at
    ON aion_conformance_findings (created_at);

CREATE TABLE IF NOT EXISTS aion_extension_readiness_assessments (
    readiness_assessment_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    extension_package_id TEXT NULL,
    module_slot_id TEXT NULL,
    capability_binding_id TEXT NULL,
    status TEXT NOT NULL,
    readiness_level TEXT NOT NULL,
    activation_ready BOOLEAN NOT NULL,
    minimum_score DOUBLE PRECISION NOT NULL,
    actual_score DOUBLE PRECISION NOT NULL,
    conformance_run_ids JSONB NOT NULL,
    compatibility_run_ids JSONB NOT NULL,
    validation_run_ids JSONB NOT NULL,
    blocker_refs JSONB NOT NULL,
    warning_refs JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_readiness_trace
    ON aion_extension_readiness_assessments (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_actor
    ON aion_extension_readiness_assessments (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_workspace
    ON aion_extension_readiness_assessments (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_extension
    ON aion_extension_readiness_assessments (extension_package_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_slot
    ON aion_extension_readiness_assessments (module_slot_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_binding
    ON aion_extension_readiness_assessments (capability_binding_id);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_status
    ON aion_extension_readiness_assessments (status);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_level
    ON aion_extension_readiness_assessments (readiness_level);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_activation
    ON aion_extension_readiness_assessments (activation_ready);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_score
    ON aion_extension_readiness_assessments (actual_score);
CREATE INDEX IF NOT EXISTS ix_aion_readiness_created_at
    ON aion_extension_readiness_assessments (created_at);
