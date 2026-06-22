CREATE TABLE IF NOT EXISTS aion_experience_records (
  experience_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  experience_type TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  outcome_refs JSONB NOT NULL,
  decision_refs JSONB NOT NULL,
  command_refs JSONB NOT NULL,
  workflow_refs JSONB NOT NULL,
  regression_refs JSONB NOT NULL,
  replay_refs JSONB NOT NULL,
  audit_refs JSONB NOT NULL,
  signal_refs JSONB NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_experience_records_trace_id ON aion_experience_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_actor_id ON aion_experience_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_workspace_id ON aion_experience_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_source_type ON aion_experience_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_source_id ON aion_experience_records(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_experience_type ON aion_experience_records(experience_type);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_status ON aion_experience_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_score ON aion_experience_records(score);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_confidence ON aion_experience_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_observed_at ON aion_experience_records(observed_at);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_created_at ON aion_experience_records(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_experience_records_deleted_at ON aion_experience_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_learning_patterns (
  pattern_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  pattern_type TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  experience_refs JSONB NOT NULL,
  outcome_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  frequency INTEGER NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  severity TEXT NOT NULL,
  recommendation TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_trace_id ON aion_learning_patterns(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_pattern_type ON aion_learning_patterns(pattern_type);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_status ON aion_learning_patterns(status);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_frequency ON aion_learning_patterns(frequency);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_confidence ON aion_learning_patterns(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_severity ON aion_learning_patterns(severity);
CREATE INDEX IF NOT EXISTS ix_aion_learning_patterns_created_at ON aion_learning_patterns(created_at);

CREATE TABLE IF NOT EXISTS aion_lesson_records (
  lesson_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  lesson_type TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  lesson TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  pattern_refs JSONB NOT NULL,
  experience_refs JSONB NOT NULL,
  outcome_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  applicability JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_lesson_records_trace_id ON aion_lesson_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lesson_records_lesson_type ON aion_lesson_records(lesson_type);
CREATE INDEX IF NOT EXISTS ix_aion_lesson_records_status ON aion_lesson_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_lesson_records_confidence ON aion_lesson_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_lesson_records_created_at ON aion_lesson_records(created_at);

CREATE TABLE IF NOT EXISTS aion_learning_synthesis_runs (
  synthesis_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  input_refs JSONB NOT NULL,
  experience_ids JSONB NOT NULL,
  pattern_ids JSONB NOT NULL,
  lesson_ids JSONB NOT NULL,
  reflection_candidate_ids JSONB NOT NULL,
  skill_candidate_suggestion_ids JSONB NOT NULL,
  regression_candidate_suggestion_ids JSONB NOT NULL,
  result JSONB NOT NULL,
  warnings JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_trace_id ON aion_learning_synthesis_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_actor_id ON aion_learning_synthesis_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_workspace_id ON aion_learning_synthesis_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_status ON aion_learning_synthesis_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_mode ON aion_learning_synthesis_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_learning_synthesis_runs_created_at ON aion_learning_synthesis_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_pattern_mining_runs (
  pattern_mining_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  mining_type TEXT NOT NULL,
  input_experience_ids JSONB NOT NULL,
  pattern_ids JSONB NOT NULL,
  skipped INTEGER NOT NULL,
  failed INTEGER NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_trace_id ON aion_pattern_mining_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_actor_id ON aion_pattern_mining_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_workspace_id ON aion_pattern_mining_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_status ON aion_pattern_mining_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_mining_type ON aion_pattern_mining_runs(mining_type);
CREATE INDEX IF NOT EXISTS ix_aion_pattern_mining_runs_created_at ON aion_pattern_mining_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_skill_candidate_suggestions (
  suggestion_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  pattern_id TEXT NULL,
  lesson_id TEXT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  proposed_skill_type TEXT NOT NULL,
  source_refs JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  promotion_allowed BOOLEAN NOT NULL,
  skill_candidate_id TEXT NULL,
  approval_request_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_trace_id ON aion_skill_candidate_suggestions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_pattern_id ON aion_skill_candidate_suggestions(pattern_id);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_lesson_id ON aion_skill_candidate_suggestions(lesson_id);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_status ON aion_skill_candidate_suggestions(status);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_proposed_skill_type ON aion_skill_candidate_suggestions(proposed_skill_type);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_risk_level ON aion_skill_candidate_suggestions(risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_confidence ON aion_skill_candidate_suggestions(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_promotion_allowed ON aion_skill_candidate_suggestions(promotion_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_skill_candidate_suggestions_created_at ON aion_skill_candidate_suggestions(created_at);

CREATE TABLE IF NOT EXISTS aion_regression_candidate_suggestions (
  regression_suggestion_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  pattern_id TEXT NULL,
  outcome_id TEXT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  source_refs JSONB NOT NULL,
  severity TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  regression_case_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_trace_id ON aion_regression_candidate_suggestions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_pattern_id ON aion_regression_candidate_suggestions(pattern_id);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_outcome_id ON aion_regression_candidate_suggestions(outcome_id);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_status ON aion_regression_candidate_suggestions(status);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_severity ON aion_regression_candidate_suggestions(severity);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_confidence ON aion_regression_candidate_suggestions(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_regression_candidate_suggestions_created_at ON aion_regression_candidate_suggestions(created_at);
