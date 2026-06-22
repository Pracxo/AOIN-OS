CREATE TABLE IF NOT EXISTS aion_model_output_records (
    model_output_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    prompt_packet_id TEXT NULL,
    model_input_manifest_id TEXT NULL,
    model_route TEXT NULL,
    provider_type TEXT NULL,
    status TEXT NOT NULL,
    output_type TEXT NOT NULL,
    raw_output_hash TEXT NOT NULL,
    redacted_output TEXT NOT NULL,
    output_redacted BOOLEAN NOT NULL,
    token_estimate INTEGER NOT NULL,
    char_count INTEGER NOT NULL,
    safety_findings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_trace_id
    ON aion_model_output_records (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_actor_id
    ON aion_model_output_records (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_workspace_id
    ON aion_model_output_records (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_prompt_packet_id
    ON aion_model_output_records (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_model_input_manifest_id
    ON aion_model_output_records (model_input_manifest_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_model_route
    ON aion_model_output_records (model_route);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_provider_type
    ON aion_model_output_records (provider_type);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_status
    ON aion_model_output_records (status);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_output_type
    ON aion_model_output_records (output_type);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_raw_output_hash
    ON aion_model_output_records (raw_output_hash);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_created_at
    ON aion_model_output_records (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_model_outputs_deleted_at
    ON aion_model_output_records (deleted_at);

CREATE TABLE IF NOT EXISTS aion_model_output_segments (
    output_segment_id TEXT PRIMARY KEY,
    model_output_id TEXT NOT NULL REFERENCES aion_model_output_records(model_output_id),
    trace_id TEXT NULL,
    segment_order INTEGER NOT NULL,
    segment_type TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    unsafe BOOLEAN NOT NULL,
    findings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_output_segments_model_output_id
    ON aion_model_output_segments (model_output_id);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_trace_id
    ON aion_model_output_segments (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_segment_order
    ON aion_model_output_segments (segment_order);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_segment_type
    ON aion_model_output_segments (segment_type);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_content_hash
    ON aion_model_output_segments (content_hash);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_confidence
    ON aion_model_output_segments (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_unsafe
    ON aion_model_output_segments (unsafe);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_created_at
    ON aion_model_output_segments (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_output_segments_deleted_at
    ON aion_model_output_segments (deleted_at);

CREATE TABLE IF NOT EXISTS aion_structured_output_validations (
    structured_validation_id TEXT PRIMARY KEY,
    model_output_id TEXT NOT NULL REFERENCES aion_model_output_records(model_output_id),
    trace_id TEXT NULL,
    schema_name TEXT NULL,
    status TEXT NOT NULL,
    valid BOOLEAN NOT NULL,
    parsed_payload JSONB NOT NULL,
    schema_errors JSONB NOT NULL,
    safety_errors JSONB NOT NULL,
    warnings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_model_output_id
    ON aion_structured_output_validations (model_output_id);
CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_trace_id
    ON aion_structured_output_validations (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_schema_name
    ON aion_structured_output_validations (schema_name);
CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_status
    ON aion_structured_output_validations (status);
CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_valid
    ON aion_structured_output_validations (valid);
CREATE INDEX IF NOT EXISTS ix_aion_structured_validations_created_at
    ON aion_structured_output_validations (created_at);

CREATE TABLE IF NOT EXISTS aion_response_candidates (
    response_candidate_id TEXT PRIMARY KEY,
    model_output_id TEXT NULL,
    trace_id TEXT NULL,
    dialogue_session_id TEXT NULL,
    prompt_packet_id TEXT NULL,
    status TEXT NOT NULL,
    response_type TEXT NOT NULL,
    content TEXT NOT NULL,
    content_hash TEXT NOT NULL,
    grounded BOOLEAN NOT NULL,
    citation_refs JSONB NOT NULL,
    grounding_refs JSONB NOT NULL,
    belief_refs JSONB NOT NULL,
    entity_refs JSONB NOT NULL,
    unsupported_statement_refs JSONB NOT NULL,
    verification_refs JSONB NOT NULL,
    confidence DOUBLE PRECISION NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    constraints JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    promoted_response_id TEXT NULL,
    deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_model_output_id
    ON aion_response_candidates (model_output_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_trace_id
    ON aion_response_candidates (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_dialogue_session_id
    ON aion_response_candidates (dialogue_session_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_prompt_packet_id
    ON aion_response_candidates (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_status
    ON aion_response_candidates (status);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_response_type
    ON aion_response_candidates (response_type);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_grounded
    ON aion_response_candidates (grounded);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_confidence
    ON aion_response_candidates (confidence);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_score
    ON aion_response_candidates (score);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_created_at
    ON aion_response_candidates (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_response_candidates_deleted_at
    ON aion_response_candidates (deleted_at);

CREATE TABLE IF NOT EXISTS aion_tool_intent_candidates (
    tool_intent_id TEXT PRIMARY KEY,
    model_output_id TEXT NULL,
    trace_id TEXT NULL,
    prompt_packet_id TEXT NULL,
    status TEXT NOT NULL,
    intent_type TEXT NOT NULL,
    tool_name TEXT NULL,
    action_type TEXT NULL,
    target_type TEXT NULL,
    target_id TEXT NULL,
    arguments_redacted JSONB NOT NULL,
    raw_arguments_hash TEXT NULL,
    risk_level TEXT NOT NULL,
    policy_decision_id TEXT NULL,
    autonomy_decision_id TEXT NULL,
    approval_request_id TEXT NULL,
    blocked_reason TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_model_output_id
    ON aion_tool_intent_candidates (model_output_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_trace_id
    ON aion_tool_intent_candidates (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_prompt_packet_id
    ON aion_tool_intent_candidates (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_status
    ON aion_tool_intent_candidates (status);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_intent_type
    ON aion_tool_intent_candidates (intent_type);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_tool_name
    ON aion_tool_intent_candidates (tool_name);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_action_type
    ON aion_tool_intent_candidates (action_type);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_target_type
    ON aion_tool_intent_candidates (target_type);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_risk_level
    ON aion_tool_intent_candidates (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_tool_intents_created_at
    ON aion_tool_intent_candidates (created_at);

CREATE TABLE IF NOT EXISTS aion_output_governance_runs (
    output_governance_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    model_output_id TEXT NOT NULL REFERENCES aion_model_output_records(model_output_id),
    status TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    parsed_segment_ids JSONB NOT NULL,
    response_candidate_ids JSONB NOT NULL,
    tool_intent_ids JSONB NOT NULL,
    structured_validation_ids JSONB NOT NULL,
    blocked BOOLEAN NOT NULL,
    issues JSONB NOT NULL,
    constraints JSONB NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    result JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_output_governance_trace_id
    ON aion_output_governance_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_output_governance_model_output_id
    ON aion_output_governance_runs (model_output_id);
CREATE INDEX IF NOT EXISTS ix_aion_output_governance_status
    ON aion_output_governance_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_output_governance_blocked
    ON aion_output_governance_runs (blocked);
CREATE INDEX IF NOT EXISTS ix_aion_output_governance_score
    ON aion_output_governance_runs (score);
CREATE INDEX IF NOT EXISTS ix_aion_output_governance_created_at
    ON aion_output_governance_runs (created_at);
