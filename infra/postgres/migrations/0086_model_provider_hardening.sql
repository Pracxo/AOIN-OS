CREATE TABLE IF NOT EXISTS aion_model_provider_profiles (
    provider_profile_id TEXT PRIMARY KEY,
    provider_key TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    status TEXT NOT NULL,
    provider_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    supported_model_families JSONB NOT NULL,
    supported_modes JSONB NOT NULL,
    declared_capabilities JSONB NOT NULL,
    required_settings JSONB NOT NULL,
    required_policy_actions JSONB NOT NULL,
    egress_requirements JSONB NOT NULL,
    output_governance_requirements JSONB NOT NULL,
    grounding_requirements JSONB NOT NULL,
    tool_use_policy JSONB NOT NULL,
    risk_level TEXT NOT NULL,
    external_calls_allowed BOOLEAN NOT NULL,
    credentials_required BOOLEAN NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_key ON aion_model_provider_profiles (provider_key);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_status ON aion_model_provider_profiles (status);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_type ON aion_model_provider_profiles (provider_type);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_risk ON aion_model_provider_profiles (risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_external ON aion_model_provider_profiles (external_calls_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_credentials ON aion_model_provider_profiles (credentials_required);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_profiles_created ON aion_model_provider_profiles (created_at);

CREATE TABLE IF NOT EXISTS aion_prompt_egress_previews (
    prompt_egress_preview_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    provider_profile_id TEXT NULL,
    provider_key TEXT NOT NULL,
    status TEXT NOT NULL,
    preview_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    prompt_packet_ref TEXT NULL,
    input_manifest_ref TEXT NULL,
    redacted_prompt_summary JSONB NOT NULL,
    blocked_fields JSONB NOT NULL,
    egress_allowed BOOLEAN NOT NULL,
    external_call_allowed BOOLEAN NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_trace ON aion_prompt_egress_previews (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_actor ON aion_prompt_egress_previews (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_workspace ON aion_prompt_egress_previews (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_profile ON aion_prompt_egress_previews (provider_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_key ON aion_prompt_egress_previews (provider_key);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_status ON aion_prompt_egress_previews (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_type ON aion_prompt_egress_previews (preview_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_egress ON aion_prompt_egress_previews (egress_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_external ON aion_prompt_egress_previews (external_call_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_egress_previews_created ON aion_prompt_egress_previews (created_at);

CREATE TABLE IF NOT EXISTS aion_model_provider_simulations (
    provider_simulation_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    provider_profile_id TEXT NULL,
    provider_key TEXT NOT NULL,
    status TEXT NOT NULL,
    simulation_type TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    input_manifest_ref TEXT NULL,
    egress_preview_id TEXT NULL,
    simulated_request_hash TEXT NOT NULL,
    simulated_response_hash TEXT NOT NULL,
    redacted_simulated_request JSONB NOT NULL,
    redacted_simulated_response JSONB NOT NULL,
    output_governance_status TEXT NOT NULL,
    tool_intent_status TEXT NOT NULL,
    grounding_status TEXT NOT NULL,
    external_calls_made BOOLEAN NOT NULL,
    credentials_used BOOLEAN NOT NULL,
    model_invoked BOOLEAN NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    blockers JSONB NOT NULL,
    warnings JSONB NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_trace ON aion_model_provider_simulations (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_profile ON aion_model_provider_simulations (provider_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_key ON aion_model_provider_simulations (provider_key);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_status ON aion_model_provider_simulations (status);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_type ON aion_model_provider_simulations (simulation_type);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_output ON aion_model_provider_simulations (output_governance_status);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_tool ON aion_model_provider_simulations (tool_intent_status);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_grounding ON aion_model_provider_simulations (grounding_status);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_external ON aion_model_provider_simulations (external_calls_made);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_credentials ON aion_model_provider_simulations (credentials_used);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_invoked ON aion_model_provider_simulations (model_invoked);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_score ON aion_model_provider_simulations (score);
CREATE INDEX IF NOT EXISTS ix_aion_model_provider_simulations_created ON aion_model_provider_simulations (created_at);

CREATE TABLE IF NOT EXISTS aion_model_provider_readiness_assessments (
    provider_readiness_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    actor_id TEXT NULL,
    workspace_id TEXT NULL,
    provider_profile_id TEXT NULL,
    provider_key TEXT NOT NULL,
    status TEXT NOT NULL,
    readiness_level TEXT NOT NULL,
    owner_scope JSONB NOT NULL,
    external_call_ready BOOLEAN NOT NULL,
    credentials_ready BOOLEAN NOT NULL,
    egress_guard_ready BOOLEAN NOT NULL,
    output_governance_ready BOOLEAN NOT NULL,
    tool_intent_guard_ready BOOLEAN NOT NULL,
    grounding_ready BOOLEAN NOT NULL,
    policy_ready BOOLEAN NOT NULL,
    audit_ready BOOLEAN NOT NULL,
    blocker_refs JSONB NOT NULL,
    warning_refs JSONB NOT NULL,
    simulation_refs JSONB NOT NULL,
    recommendations JSONB NOT NULL,
    score DOUBLE PRECISION NOT NULL,
    metadata JSONB NOT NULL,
    created_by TEXT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_trace ON aion_model_provider_readiness_assessments (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_profile ON aion_model_provider_readiness_assessments (provider_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_key ON aion_model_provider_readiness_assessments (provider_key);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_status ON aion_model_provider_readiness_assessments (status);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_level ON aion_model_provider_readiness_assessments (readiness_level);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_external ON aion_model_provider_readiness_assessments (external_call_ready);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_credentials ON aion_model_provider_readiness_assessments (credentials_ready);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_score ON aion_model_provider_readiness_assessments (score);
CREATE INDEX IF NOT EXISTS ix_aion_provider_readiness_created ON aion_model_provider_readiness_assessments (created_at);

CREATE TABLE IF NOT EXISTS aion_model_provider_blockers (
    provider_blocker_id TEXT PRIMARY KEY,
    trace_id TEXT NULL,
    provider_profile_id TEXT NULL,
    provider_key TEXT NULL,
    source_type TEXT NULL,
    source_id TEXT NULL,
    blocker_type TEXT NOT NULL,
    severity TEXT NOT NULL,
    status TEXT NOT NULL,
    reason TEXT NOT NULL,
    recommended_action TEXT NOT NULL,
    metadata JSONB NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
    resolved_at TIMESTAMPTZ NULL,
    dismissed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_trace ON aion_model_provider_blockers (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_profile ON aion_model_provider_blockers (provider_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_key ON aion_model_provider_blockers (provider_key);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_source_type ON aion_model_provider_blockers (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_source_id ON aion_model_provider_blockers (source_id);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_type ON aion_model_provider_blockers (blocker_type);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_severity ON aion_model_provider_blockers (severity);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_status ON aion_model_provider_blockers (status);
CREATE INDEX IF NOT EXISTS ix_aion_provider_blockers_created ON aion_model_provider_blockers (created_at);
