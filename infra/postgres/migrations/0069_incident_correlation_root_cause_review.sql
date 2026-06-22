CREATE TABLE IF NOT EXISTS aion_incident_records (
    incident_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    incident_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    primary_signal_type TEXT NULL,
    primary_signal_id TEXT NULL,
    signal_refs JSONB NOT NULL,
    alert_refs JSONB NOT NULL,
    notification_refs JSONB NOT NULL,
    run_refs JSONB NOT NULL,
    action_refs JSONB NOT NULL,
    model_output_refs JSONB NOT NULL,
    prompt_refs JSONB NOT NULL,
    grounding_refs JSONB NOT NULL,
    security_refs JSONB NOT NULL,
    audit_refs JSONB NOT NULL,
    scheduler_refs JSONB NOT NULL,
    outcome_refs JSONB NOT NULL,
    learning_refs JSONB NOT NULL,
    blocker_refs JSONB NOT NULL,
    root_cause_candidate_refs JSONB NOT NULL,
    recovery_review_refs JSONB NOT NULL,
    related_incident_ids JSONB NOT NULL,
    correlation_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    acknowledged_at TIMESTAMPTZ NULL,
    resolved_at TIMESTAMPTZ NULL,
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_incident_records_trace_id ON aion_incident_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_workspace_id ON aion_incident_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_status ON aion_incident_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_incident_type ON aion_incident_records(incident_type);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_severity ON aion_incident_records(severity);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_correlation_key ON aion_incident_records(correlation_key);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_fingerprint ON aion_incident_records(fingerprint);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_created_at ON aion_incident_records(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_incident_records_updated_at ON aion_incident_records(updated_at);

CREATE TABLE IF NOT EXISTS aion_incident_signals (
    incident_signal_id TEXT PRIMARY KEY,
    incident_id TEXT NULL,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    signal_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    correlation_key TEXT NOT NULL,
    fingerprint TEXT NOT NULL,
    refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    occurred_at TIMESTAMPTZ NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    linked_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_incident_id ON aion_incident_signals(incident_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_trace_id ON aion_incident_signals(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_workspace_id ON aion_incident_signals(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_source_type ON aion_incident_signals(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_source_id ON aion_incident_signals(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_signal_type ON aion_incident_signals(signal_type);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_severity ON aion_incident_signals(severity);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_status ON aion_incident_signals(status);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_correlation_key ON aion_incident_signals(correlation_key);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_fingerprint ON aion_incident_signals(fingerprint);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_occurred_at ON aion_incident_signals(occurred_at);
CREATE INDEX IF NOT EXISTS ix_aion_incident_signals_created_at ON aion_incident_signals(created_at);

CREATE TABLE IF NOT EXISTS aion_incident_correlation_rules (
    correlation_rule_id TEXT PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    rule_type TEXT NOT NULL,
    severity_threshold TEXT NOT NULL,
    source_types JSONB NOT NULL,
    signal_types JSONB NOT NULL,
    window_seconds INTEGER NOT NULL,
    grouping_fields JSONB NOT NULL,
    conditions JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_name ON aion_incident_correlation_rules(name);
CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_status ON aion_incident_correlation_rules(status);
CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_rule_type ON aion_incident_correlation_rules(rule_type);
CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_severity_threshold ON aion_incident_correlation_rules(severity_threshold);
CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_window_seconds ON aion_incident_correlation_rules(window_seconds);
CREATE INDEX IF NOT EXISTS ix_aion_incident_rules_created_at ON aion_incident_correlation_rules(created_at);

CREATE TABLE IF NOT EXISTS aion_incident_correlation_runs (
    correlation_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    window_start TIMESTAMPTZ NULL,
    window_end TIMESTAMPTZ NULL,
    rules_applied JSONB NOT NULL,
    signals_seen INTEGER NOT NULL,
    signals_linked INTEGER NOT NULL,
    incidents_created INTEGER NOT NULL,
    incidents_updated INTEGER NOT NULL,
    incidents_unchanged INTEGER NOT NULL,
    incidents JSONB NOT NULL,
    warnings JSONB NOT NULL,
    failures JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_incident_runs_trace_id ON aion_incident_correlation_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_runs_workspace_id ON aion_incident_correlation_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_incident_runs_status ON aion_incident_correlation_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_incident_runs_mode ON aion_incident_correlation_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_incident_runs_created_at ON aion_incident_correlation_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_root_cause_candidates (
    root_cause_candidate_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    candidate_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    title TEXT NOT NULL,
    hypothesis TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    supporting_refs JSONB NOT NULL,
    opposing_refs JSONB NOT NULL,
    missing_evidence JSONB NOT NULL,
    recommended_checks JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    confirmed_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_root_causes_incident_id ON aion_root_cause_candidates(incident_id);
CREATE INDEX IF NOT EXISTS ix_aion_root_causes_trace_id ON aion_root_cause_candidates(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_root_causes_status ON aion_root_cause_candidates(status);
CREATE INDEX IF NOT EXISTS ix_aion_root_causes_candidate_type ON aion_root_cause_candidates(candidate_type);
CREATE INDEX IF NOT EXISTS ix_aion_root_causes_severity ON aion_root_cause_candidates(severity);
CREATE INDEX IF NOT EXISTS ix_aion_root_causes_created_at ON aion_root_cause_candidates(created_at);

CREATE TABLE IF NOT EXISTS aion_recovery_review_records (
    recovery_review_id TEXT PRIMARY KEY,
    incident_id TEXT NOT NULL,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    review_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    action_proposal_refs JSONB NOT NULL,
    compensation_plan_refs JSONB NOT NULL,
    notification_refs JSONB NOT NULL,
    outcome_refs JSONB NOT NULL,
    created_records JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_recovery_reviews_incident_id ON aion_recovery_review_records(incident_id);
CREATE INDEX IF NOT EXISTS ix_aion_recovery_reviews_trace_id ON aion_recovery_review_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_recovery_reviews_status ON aion_recovery_review_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_recovery_reviews_review_type ON aion_recovery_review_records(review_type);
CREATE INDEX IF NOT EXISTS ix_aion_recovery_reviews_created_at ON aion_recovery_review_records(created_at);
