CREATE TABLE IF NOT EXISTS aion_release_candidates (
    release_candidate_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    rc_key TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    source_ref TEXT NULL,
    commit_ref TEXT NULL,
    tag_ref TEXT NULL,
    verification_matrix_id TEXT NULL,
    rc_run_id TEXT NULL,
    rc_report_id TEXT NULL,
    freeze_gate_id TEXT NULL,
    release_package_id TEXT NULL,
    readiness_score DOUBLE PRECISION NOT NULL,
    release_ready BOOLEAN NOT NULL,
    blocker_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    evidence_pack_ref TEXT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    archived_at TIMESTAMPTZ NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_key ON aion_release_candidates (rc_key);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_version ON aion_release_candidates (version);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_status ON aion_release_candidates (status);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_trace ON aion_release_candidates (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_score ON aion_release_candidates (readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_ready ON aion_release_candidates (release_ready);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_blockers ON aion_release_candidates (blocker_count);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_created_at ON aion_release_candidates (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_release_candidates_deleted_at ON aion_release_candidates (deleted_at);
CREATE UNIQUE INDEX IF NOT EXISTS uq_aion_release_candidates_key_active
    ON aion_release_candidates (rc_key)
    WHERE deleted_at IS NULL;

CREATE TABLE IF NOT EXISTS aion_rc_verification_checks (
    verification_check_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    rc_run_id TEXT NULL,
    check_key TEXT NOT NULL,
    check_type TEXT NOT NULL,
    status TEXT NOT NULL,
    severity TEXT NOT NULL,
    required BOOLEAN NOT NULL,
    passed BOOLEAN NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    command_hint TEXT NULL,
    evidence JSONB NOT NULL,
    duration_ms INTEGER NULL,
    error JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_trace ON aion_rc_verification_checks (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_run ON aion_rc_verification_checks (rc_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_key ON aion_rc_verification_checks (check_key);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_type ON aion_rc_verification_checks (check_type);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_status ON aion_rc_verification_checks (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_severity ON aion_rc_verification_checks (severity);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_required ON aion_rc_verification_checks (required);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_passed ON aion_rc_verification_checks (passed);
CREATE INDEX IF NOT EXISTS ix_aion_rc_checks_created_at ON aion_rc_verification_checks (created_at);

CREATE TABLE IF NOT EXISTS aion_rc_verification_matrices (
    verification_matrix_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    matrix_key TEXT NOT NULL,
    version TEXT NOT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    required_checks JSONB NOT NULL,
    optional_checks JSONB NOT NULL,
    required_threshold DOUBLE PRECISION NOT NULL,
    release_ready_threshold DOUBLE PRECISION NOT NULL,
    fail_on_critical BOOLEAN NOT NULL,
    fail_on_missing_required BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL,
    UNIQUE (matrix_key, version)
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_key ON aion_rc_verification_matrices (matrix_key);
CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_version ON aion_rc_verification_matrices (version);
CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_status ON aion_rc_verification_matrices (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_required_threshold ON aion_rc_verification_matrices (required_threshold);
CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_release_threshold ON aion_rc_verification_matrices (release_ready_threshold);
CREATE INDEX IF NOT EXISTS ix_aion_rc_matrices_created_at ON aion_rc_verification_matrices (created_at);

CREATE TABLE IF NOT EXISTS aion_rc_gate_runs (
    rc_run_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    release_candidate_id TEXT NULL,
    verification_matrix_id TEXT NULL,
    status TEXT NOT NULL,
    mode TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL,
    checks_total INTEGER NOT NULL,
    checks_passed INTEGER NOT NULL,
    checks_failed INTEGER NOT NULL,
    checks_warning INTEGER NOT NULL,
    checks_skipped INTEGER NOT NULL,
    blocker_count INTEGER NOT NULL,
    readiness_score DOUBLE PRECISION NOT NULL,
    release_ready BOOLEAN NOT NULL,
    verification_check_ids JSONB NOT NULL,
    finding_ids JSONB NOT NULL,
    evidence_pack_id TEXT NULL,
    warnings JSONB NOT NULL,
    failures JSONB NOT NULL,
    result JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_trace ON aion_rc_gate_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_actor ON aion_rc_gate_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_workspace ON aion_rc_gate_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_candidate ON aion_rc_gate_runs (release_candidate_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_matrix ON aion_rc_gate_runs (verification_matrix_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_status ON aion_rc_gate_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_mode ON aion_rc_gate_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_score ON aion_rc_gate_runs (readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_ready ON aion_rc_gate_runs (release_ready);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_blockers ON aion_rc_gate_runs (blocker_count);
CREATE INDEX IF NOT EXISTS ix_aion_rc_runs_created_at ON aion_rc_gate_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_rc_findings (
    rc_finding_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    rc_run_id TEXT NULL,
    release_candidate_id TEXT NULL,
    finding_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    blocking BOOLEAN NOT NULL,
    title TEXT NOT NULL,
    description TEXT NOT NULL,
    check_key TEXT NULL,
    source_type TEXT NULL,
    source_id TEXT NULL,
    recommended_action TEXT NOT NULL,
    evidence_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_trace ON aion_rc_findings (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_run ON aion_rc_findings (rc_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_candidate ON aion_rc_findings (release_candidate_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_type ON aion_rc_findings (finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_severity ON aion_rc_findings (severity);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_status ON aion_rc_findings (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_blocking ON aion_rc_findings (blocking);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_check_key ON aion_rc_findings (check_key);
CREATE INDEX IF NOT EXISTS ix_aion_rc_findings_created_at ON aion_rc_findings (created_at);

CREATE TABLE IF NOT EXISTS aion_rc_evidence_packs (
    evidence_pack_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    rc_run_id TEXT NULL,
    release_candidate_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    pack_type TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    evidence_refs JSONB NOT NULL,
    check_summaries JSONB NOT NULL,
    artifact_refs JSONB NOT NULL,
    report_hash TEXT NOT NULL,
    redacted_report JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_trace ON aion_rc_evidence_packs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_run ON aion_rc_evidence_packs (rc_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_candidate ON aion_rc_evidence_packs (release_candidate_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_status ON aion_rc_evidence_packs (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_type ON aion_rc_evidence_packs (pack_type);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_hash ON aion_rc_evidence_packs (report_hash);
CREATE INDEX IF NOT EXISTS ix_aion_rc_packs_created_at ON aion_rc_evidence_packs (created_at);

CREATE TABLE IF NOT EXISTS aion_rc_reports (
    rc_report_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    release_candidate_id TEXT NULL,
    rc_run_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    version TEXT NOT NULL,
    readiness_score DOUBLE PRECISION NOT NULL,
    release_ready BOOLEAN NOT NULL,
    blocker_count INTEGER NOT NULL,
    warning_count INTEGER NOT NULL,
    passed_checks JSONB NOT NULL,
    failed_checks JSONB NOT NULL,
    warning_checks JSONB NOT NULL,
    findings JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    report JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_trace ON aion_rc_reports (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_candidate ON aion_rc_reports (release_candidate_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_run ON aion_rc_reports (rc_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_status ON aion_rc_reports (status);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_version ON aion_rc_reports (version);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_score ON aion_rc_reports (readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_ready ON aion_rc_reports (release_ready);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_blockers ON aion_rc_reports (blocker_count);
CREATE INDEX IF NOT EXISTS ix_aion_rc_reports_created_at ON aion_rc_reports (created_at);
