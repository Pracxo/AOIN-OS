CREATE TABLE IF NOT EXISTS aion_self_model_profiles (
    self_model_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    full_name TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    description TEXT NOT NULL,
    operating_principles JSONB NOT NULL,
    architecture_refs JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_self_model_profiles_name ON aion_self_model_profiles (name);
CREATE INDEX IF NOT EXISTS ix_aion_self_model_profiles_version ON aion_self_model_profiles (version);
CREATE INDEX IF NOT EXISTS ix_aion_self_model_profiles_status ON aion_self_model_profiles (status);
CREATE INDEX IF NOT EXISTS ix_aion_self_model_profiles_created_at ON aion_self_model_profiles (created_at);

CREATE TABLE IF NOT EXISTS aion_capability_awareness_records (
    awareness_id TEXT PRIMARY KEY,
    capability_key TEXT NOT NULL,
    capability_type TEXT NOT NULL,
    status TEXT NOT NULL,
    availability TEXT NOT NULL,
    mode TEXT NOT NULL,
    risk_level TEXT NOT NULL,
    requires_policy BOOLEAN NOT NULL,
    requires_approval BOOLEAN NOT NULL,
    requires_autonomy BOOLEAN NOT NULL,
    dry_run_only BOOLEAN NOT NULL,
    source_refs JSONB NOT NULL,
    limitations JSONB NOT NULL,
    metadata JSONB NOT NULL,
    checked_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_capability_key ON aion_capability_awareness_records (capability_key);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_capability_type ON aion_capability_awareness_records (capability_type);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_status ON aion_capability_awareness_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_availability ON aion_capability_awareness_records (availability);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_mode ON aion_capability_awareness_records (mode);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_risk_level ON aion_capability_awareness_records (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_dry_run_only ON aion_capability_awareness_records (dry_run_only);
CREATE INDEX IF NOT EXISTS ix_aion_capability_awareness_records_checked_at ON aion_capability_awareness_records (checked_at);

CREATE TABLE IF NOT EXISTS aion_limitation_records (
    limitation_id TEXT PRIMARY KEY,
    limitation_key TEXT NOT NULL UNIQUE,
    category TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    affected_capabilities JSONB NOT NULL,
    workaround TEXT NULL,
    disclosure_required BOOLEAN NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_limitation_key ON aion_limitation_records (limitation_key);
CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_category ON aion_limitation_records (category);
CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_status ON aion_limitation_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_severity ON aion_limitation_records (severity);
CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_disclosure_required ON aion_limitation_records (disclosure_required);
CREATE INDEX IF NOT EXISTS ix_aion_limitation_records_created_at ON aion_limitation_records (created_at);

CREATE TABLE IF NOT EXISTS aion_confidence_calibration_records (
    calibration_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    response_id TEXT NULL,
    reasoning_id TEXT NULL,
    decision_frame_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    confidence_level TEXT NOT NULL,
    grounding_status TEXT NOT NULL,
    uncertainty_factors JSONB NOT NULL,
    required_disclosures JSONB NOT NULL,
    clarification_recommended BOOLEAN NOT NULL,
    verification_recommended BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_trace_id ON aion_confidence_calibration_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_response_id ON aion_confidence_calibration_records (response_id);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_reasoning_id ON aion_confidence_calibration_records (reasoning_id);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_decision_frame_id ON aion_confidence_calibration_records (decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_source_type ON aion_confidence_calibration_records (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_source_id ON aion_confidence_calibration_records (source_id);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_confidence ON aion_confidence_calibration_records (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_confidence_level ON aion_confidence_calibration_records (confidence_level);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_grounding_status ON aion_confidence_calibration_records (grounding_status);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_clarification_recommended ON aion_confidence_calibration_records (clarification_recommended);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_verification_recommended ON aion_confidence_calibration_records (verification_recommended);
CREATE INDEX IF NOT EXISTS ix_aion_confidence_calibration_records_created_at ON aion_confidence_calibration_records (created_at);

CREATE TABLE IF NOT EXISTS aion_self_assessment_runs (
    self_assessment_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    assessment_type TEXT NOT NULL,
    capability_count INTEGER NOT NULL,
    active_capability_count INTEGER NOT NULL,
    disabled_capability_count INTEGER NOT NULL,
    unavailable_capability_count INTEGER NOT NULL,
    limitation_count INTEGER NOT NULL,
    critical_limitation_count INTEGER NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    report JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_self_assessment_runs_trace_id ON aion_self_assessment_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_self_assessment_runs_status ON aion_self_assessment_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_self_assessment_runs_assessment_type ON aion_self_assessment_runs (assessment_type);
CREATE INDEX IF NOT EXISTS ix_aion_self_assessment_runs_created_at ON aion_self_assessment_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_introspection_snapshots (
    introspection_snapshot_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    snapshot_type TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    self_model JSONB NOT NULL,
    capability_inventory JSONB NOT NULL,
    limitations JSONB NOT NULL,
    calibration_summary JSONB NOT NULL,
    operator_summary JSONB NOT NULL,
    config_summary JSONB NOT NULL,
    audit_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_trace_id ON aion_introspection_snapshots (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_actor_id ON aion_introspection_snapshots (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_workspace_id ON aion_introspection_snapshots (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_snapshot_type ON aion_introspection_snapshots (snapshot_type);
CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_status ON aion_introspection_snapshots (status);
CREATE INDEX IF NOT EXISTS ix_aion_introspection_snapshots_created_at ON aion_introspection_snapshots (created_at);
