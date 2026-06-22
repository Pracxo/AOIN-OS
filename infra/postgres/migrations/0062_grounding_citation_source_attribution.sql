CREATE TABLE IF NOT EXISTS aion_grounding_sources (
    grounding_source_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    title TEXT NOT NULL,
    summary TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    sensitivity TEXT NOT NULL,
    trust_level TEXT NOT NULL,
    evidence_refs JSONB NOT NULL,
    belief_refs JSONB NOT NULL,
    memory_refs JSONB NOT NULL,
    entity_refs JSONB NOT NULL,
    provenance_refs JSONB NOT NULL,
    owner_scope JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_trace_id ON aion_grounding_sources(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_source_type ON aion_grounding_sources(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_source_id ON aion_grounding_sources(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_content_hash ON aion_grounding_sources(content_hash);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_sensitivity ON aion_grounding_sources(sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_trust_level ON aion_grounding_sources(trust_level);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_created_at ON aion_grounding_sources(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_sources_deleted_at ON aion_grounding_sources(deleted_at);

CREATE TABLE IF NOT EXISTS aion_citation_records (
    citation_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    response_id TEXT NULL,
    explanation_id TEXT NULL,
    source_type TEXT NOT NULL,
    source_id TEXT NOT NULL,
    grounding_source_id TEXT NULL,
    citation_type TEXT NOT NULL,
    label TEXT NOT NULL,
    quote TEXT NULL,
    start_char INTEGER NULL,
    end_char INTEGER NULL,
    confidence DOUBLE PRECISION NOT NULL,
    verified BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_citation_records_trace_id ON aion_citation_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_response_id ON aion_citation_records(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_explanation_id ON aion_citation_records(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_source_type ON aion_citation_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_source_id ON aion_citation_records(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_citation_type ON aion_citation_records(citation_type);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_confidence ON aion_citation_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_verified ON aion_citation_records(verified);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_created_at ON aion_citation_records(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_citation_records_deleted_at ON aion_citation_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_response_citation_maps (
    citation_map_id TEXT PRIMARY KEY,
    response_id TEXT NOT NULL,
    trace_id TEXT NULL,
    status TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    citation_ids JSONB NOT NULL,
    unsupported_statement_ids JSONB NOT NULL,
    coverage_score DOUBLE PRECISION NOT NULL,
    required_source_types JSONB NOT NULL,
    missing_source_types JSONB NOT NULL,
    constraints JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_response_id ON aion_response_citation_maps(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_trace_id ON aion_response_citation_maps(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_status ON aion_response_citation_maps(status);
CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_grounded ON aion_response_citation_maps(grounded);
CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_coverage_score ON aion_response_citation_maps(coverage_score);
CREATE INDEX IF NOT EXISTS ix_aion_response_citation_maps_created_at ON aion_response_citation_maps(created_at);

CREATE TABLE IF NOT EXISTS aion_unsupported_statements (
    unsupported_statement_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    response_id TEXT NULL,
    explanation_id TEXT NULL,
    statement_text TEXT NOT NULL,
    statement_hash TEXT NOT NULL,
    reason TEXT NOT NULL,
    severity TEXT NOT NULL,
    required_support JSONB NOT NULL,
    candidate_source_refs JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_trace_id ON aion_unsupported_statements(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_response_id ON aion_unsupported_statements(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_explanation_id ON aion_unsupported_statements(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_statement_hash ON aion_unsupported_statements(statement_hash);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_severity ON aion_unsupported_statements(severity);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_created_at ON aion_unsupported_statements(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_unsupported_statements_resolved_at ON aion_unsupported_statements(resolved_at);

CREATE TABLE IF NOT EXISTS aion_grounding_verification_runs (
    grounding_verification_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    response_id TEXT NULL,
    explanation_id TEXT NULL,
    target_type TEXT NOT NULL,
    target_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    grounded BOOLEAN NOT NULL,
    checked_statement_count INTEGER NOT NULL,
    supported_statement_count INTEGER NOT NULL,
    unsupported_statement_count INTEGER NOT NULL,
    citation_count INTEGER NOT NULL,
    coverage_score DOUBLE PRECISION NOT NULL,
    issues JSONB NOT NULL,
    result JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_trace_id ON aion_grounding_verification_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_response_id ON aion_grounding_verification_runs(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_explanation_id ON aion_grounding_verification_runs(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_target_type ON aion_grounding_verification_runs(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_target_id ON aion_grounding_verification_runs(target_id);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_status ON aion_grounding_verification_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_grounded ON aion_grounding_verification_runs(grounded);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_coverage_score ON aion_grounding_verification_runs(coverage_score);
CREATE INDEX IF NOT EXISTS ix_aion_grounding_verification_runs_created_at ON aion_grounding_verification_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_source_coverage_reports (
    source_coverage_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    response_id TEXT NULL,
    explanation_id TEXT NULL,
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    source_counts JSONB NOT NULL,
    required_source_types JSONB NOT NULL,
    missing_source_types JSONB NOT NULL,
    weak_source_refs JSONB NOT NULL,
    strong_source_refs JSONB NOT NULL,
    coverage_score DOUBLE PRECISION NOT NULL,
    recommendations JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_trace_id ON aion_source_coverage_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_response_id ON aion_source_coverage_reports(response_id);
CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_explanation_id ON aion_source_coverage_reports(explanation_id);
CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_status ON aion_source_coverage_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_coverage_score ON aion_source_coverage_reports(coverage_score);
CREATE INDEX IF NOT EXISTS ix_aion_source_coverage_reports_created_at ON aion_source_coverage_reports(created_at);
