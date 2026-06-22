CREATE TABLE IF NOT EXISTS aion_outcome_records (
  outcome_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  status TEXT NOT NULL,
  outcome_type TEXT NOT NULL,
  title TEXT NOT NULL,
  summary TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  expected_effects JSONB NOT NULL,
  observed_effects JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  situation_refs JSONB NOT NULL,
  decision_refs JSONB NOT NULL,
  execution_refs JSONB NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_trace_id ON aion_outcome_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_actor_id ON aion_outcome_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_workspace_id ON aion_outcome_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_source_type ON aion_outcome_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_source_id ON aion_outcome_records(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_status ON aion_outcome_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_outcome_type ON aion_outcome_records(outcome_type);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_confidence ON aion_outcome_records(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_score ON aion_outcome_records(score);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_observed_at ON aion_outcome_records(observed_at);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_created_at ON aion_outcome_records(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_records_deleted_at ON aion_outcome_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_expected_effects (
  expected_effect_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  effect_type TEXT NOT NULL,
  subject_ref TEXT NULL,
  predicate TEXT NOT NULL,
  object_ref TEXT NULL,
  expected_value JSONB NOT NULL,
  success_criteria JSONB NOT NULL,
  required BOOLEAN NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  owner_scope JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_trace_id ON aion_expected_effects(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_source_type ON aion_expected_effects(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_source_id ON aion_expected_effects(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_effect_type ON aion_expected_effects(effect_type);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_subject_ref ON aion_expected_effects(subject_ref);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_predicate ON aion_expected_effects(predicate);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_object_ref ON aion_expected_effects(object_ref);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_required ON aion_expected_effects(required);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_confidence ON aion_expected_effects(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_deleted_at ON aion_expected_effects(deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_expected_effects_created_at ON aion_expected_effects(created_at);

CREATE TABLE IF NOT EXISTS aion_observed_effects (
  observed_effect_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  outcome_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  effect_type TEXT NOT NULL,
  subject_ref TEXT NULL,
  predicate TEXT NOT NULL,
  object_ref TEXT NULL,
  observed_value JSONB NOT NULL,
  observation_source_type TEXT NOT NULL,
  observation_source_id TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  sensitivity TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  situation_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_trace_id ON aion_observed_effects(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_outcome_id ON aion_observed_effects(outcome_id);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_source_type ON aion_observed_effects(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_source_id ON aion_observed_effects(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_effect_type ON aion_observed_effects(effect_type);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_subject_ref ON aion_observed_effects(subject_ref);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_predicate ON aion_observed_effects(predicate);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_object_ref ON aion_observed_effects(object_ref);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_observation_source_type ON aion_observed_effects(observation_source_type);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_observation_source_id ON aion_observed_effects(observation_source_id);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_confidence ON aion_observed_effects(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_sensitivity ON aion_observed_effects(sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_observed_at ON aion_observed_effects(observed_at);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_deleted_at ON aion_observed_effects(deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_observed_effects_created_at ON aion_observed_effects(created_at);

CREATE TABLE IF NOT EXISTS aion_effect_verification_runs (
  verification_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  outcome_id TEXT NULL,
  source_type TEXT NULL,
  source_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  expected_effect_ids JSONB NOT NULL,
  observed_effect_ids JSONB NOT NULL,
  matched_effects JSONB NOT NULL,
  missing_effects JSONB NOT NULL,
  unexpected_effects JSONB NOT NULL,
  contradicted_effects JSONB NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_trace_id ON aion_effect_verification_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_outcome_id ON aion_effect_verification_runs(outcome_id);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_source_type ON aion_effect_verification_runs(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_source_id ON aion_effect_verification_runs(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_status ON aion_effect_verification_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_mode ON aion_effect_verification_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_score ON aion_effect_verification_runs(score);
CREATE INDEX IF NOT EXISTS ix_aion_effect_verification_runs_created_at ON aion_effect_verification_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_causal_attributions (
  causal_attribution_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  outcome_id TEXT NOT NULL,
  cause_type TEXT NOT NULL,
  cause_id TEXT NOT NULL,
  effect_type TEXT NOT NULL,
  effect_id TEXT NOT NULL,
  relation_type TEXT NOT NULL,
  confidence DOUBLE PRECISION NOT NULL,
  evidence_refs JSONB NOT NULL,
  reasoning TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_trace_id ON aion_causal_attributions(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_outcome_id ON aion_causal_attributions(outcome_id);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_cause_type ON aion_causal_attributions(cause_type);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_cause_id ON aion_causal_attributions(cause_id);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_effect_type ON aion_causal_attributions(effect_type);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_effect_id ON aion_causal_attributions(effect_id);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_relation_type ON aion_causal_attributions(relation_type);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_confidence ON aion_causal_attributions(confidence);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_deleted_at ON aion_causal_attributions(deleted_at);
CREATE INDEX IF NOT EXISTS ix_aion_causal_attributions_created_at ON aion_causal_attributions(created_at);

CREATE TABLE IF NOT EXISTS aion_outcome_feedback_records (
  outcome_feedback_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  outcome_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  feedback_type TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  message TEXT NOT NULL,
  recommended_followup TEXT NOT NULL,
  learning_signal_id TEXT NULL,
  reflection_id TEXT NULL,
  regression_case_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_trace_id ON aion_outcome_feedback_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_outcome_id ON aion_outcome_feedback_records(outcome_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_source_type ON aion_outcome_feedback_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_source_id ON aion_outcome_feedback_records(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_feedback_type ON aion_outcome_feedback_records(feedback_type);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_status ON aion_outcome_feedback_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_severity ON aion_outcome_feedback_records(severity);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_learning_signal_id ON aion_outcome_feedback_records(learning_signal_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_reflection_id ON aion_outcome_feedback_records(reflection_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_regression_case_id ON aion_outcome_feedback_records(regression_case_id);
CREATE INDEX IF NOT EXISTS ix_aion_outcome_feedback_created_at ON aion_outcome_feedback_records(created_at);
