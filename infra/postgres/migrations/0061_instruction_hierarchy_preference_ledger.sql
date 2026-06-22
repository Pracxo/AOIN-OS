CREATE TABLE IF NOT EXISTS aion_instruction_records (
  instruction_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  instruction_text TEXT NOT NULL,
  normalized_instruction TEXT NOT NULL,
  instruction_type TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  scope_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  priority INTEGER NOT NULL,
  status TEXT NOT NULL,
  expires_at TIMESTAMPTZ NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_trace_id
  ON aion_instruction_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_actor_id
  ON aion_instruction_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_workspace_id
  ON aion_instruction_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_instruction_type
  ON aion_instruction_records(instruction_type);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_source_type
  ON aion_instruction_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_scope_type
  ON aion_instruction_records(scope_type);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_priority
  ON aion_instruction_records(priority);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_status
  ON aion_instruction_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_expires_at
  ON aion_instruction_records(expires_at);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_records_created_at
  ON aion_instruction_records(created_at);

CREATE TABLE IF NOT EXISTS aion_preference_records (
  preference_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  preference_key TEXT NOT NULL,
  preference_type TEXT NOT NULL,
  preference_value JSONB NOT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  confirmed_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  confirmed_at TIMESTAMPTZ NULL,
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_preference_records_trace_id
  ON aion_preference_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_actor_id
  ON aion_preference_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_workspace_id
  ON aion_preference_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_preference_key
  ON aion_preference_records(preference_key);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_preference_type
  ON aion_preference_records(preference_type);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_status
  ON aion_preference_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_confidence
  ON aion_preference_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_source_type
  ON aion_preference_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_preference_records_created_at
  ON aion_preference_records(created_at);
CREATE UNIQUE INDEX IF NOT EXISTS ux_aion_preference_records_confirmed_scope_key
  ON aion_preference_records(preference_key, actor_id, workspace_id)
  WHERE status = 'confirmed';

CREATE TABLE IF NOT EXISTS aion_constraint_records (
  constraint_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  constraint_key TEXT NOT NULL,
  constraint_type TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  description TEXT NOT NULL,
  rule JSONB NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_trace_id
  ON aion_constraint_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_actor_id
  ON aion_constraint_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_workspace_id
  ON aion_constraint_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_constraint_key
  ON aion_constraint_records(constraint_key);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_constraint_type
  ON aion_constraint_records(constraint_type);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_status
  ON aion_constraint_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_severity
  ON aion_constraint_records(severity);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_source_type
  ON aion_constraint_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_constraint_records_created_at
  ON aion_constraint_records(created_at);

CREATE TABLE IF NOT EXISTS aion_style_profiles (
  style_profile_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  style_rules JSONB NOT NULL,
  formatting_rules JSONB NOT NULL,
  tone_rules JSONB NOT NULL,
  prohibited_patterns JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_style_profiles_name
  ON aion_style_profiles(name);
CREATE INDEX IF NOT EXISTS ix_aion_style_profiles_status
  ON aion_style_profiles(status);
CREATE INDEX IF NOT EXISTS ix_aion_style_profiles_actor_id
  ON aion_style_profiles(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_style_profiles_workspace_id
  ON aion_style_profiles(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_style_profiles_created_at
  ON aion_style_profiles(created_at);

CREATE TABLE IF NOT EXISTS aion_instruction_conflicts (
  conflict_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  conflict_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  instruction_ids JSONB NOT NULL,
  preference_ids JSONB NOT NULL,
  constraint_ids JSONB NOT NULL,
  reason TEXT NOT NULL,
  resolution TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_trace_id
  ON aion_instruction_conflicts(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_actor_id
  ON aion_instruction_conflicts(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_workspace_id
  ON aion_instruction_conflicts(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_conflict_type
  ON aion_instruction_conflicts(conflict_type);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_severity
  ON aion_instruction_conflicts(severity);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_status
  ON aion_instruction_conflicts(status);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_conflicts_created_at
  ON aion_instruction_conflicts(created_at);

CREATE TABLE IF NOT EXISTS aion_instruction_resolution_runs (
  resolution_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  input JSONB NOT NULL,
  applied_instruction_ids JSONB NOT NULL,
  applied_preference_ids JSONB NOT NULL,
  applied_constraint_ids JSONB NOT NULL,
  suppressed_instruction_ids JSONB NOT NULL,
  conflict_ids JSONB NOT NULL,
  effective_instructions JSONB NOT NULL,
  effective_style JSONB NOT NULL,
  constraints JSONB NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_instruction_resolution_runs_trace_id
  ON aion_instruction_resolution_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_resolution_runs_actor_id
  ON aion_instruction_resolution_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_resolution_runs_workspace_id
  ON aion_instruction_resolution_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_resolution_runs_status
  ON aion_instruction_resolution_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_instruction_resolution_runs_created_at
  ON aion_instruction_resolution_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_preference_learning_candidates (
  candidate_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  preference_key TEXT NOT NULL,
  preference_type TEXT NOT NULL,
  proposed_value JSONB NOT NULL,
  status TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  reason TEXT NOT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  evidence_refs JSONB NOT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_trace_id
  ON aion_preference_learning_candidates(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_actor_id
  ON aion_preference_learning_candidates(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_workspace_id
  ON aion_preference_learning_candidates(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_preference_key
  ON aion_preference_learning_candidates(preference_key);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_preference_type
  ON aion_preference_learning_candidates(preference_type);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_status
  ON aion_preference_learning_candidates(status);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_confidence
  ON aion_preference_learning_candidates(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_source_type
  ON aion_preference_learning_candidates(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_preference_learning_candidates_created_at
  ON aion_preference_learning_candidates(created_at);
