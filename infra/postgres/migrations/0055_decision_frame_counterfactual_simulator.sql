CREATE TABLE IF NOT EXISTS aion_decision_frames (
  decision_frame_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  frame_type TEXT NOT NULL,
  title TEXT NOT NULL,
  question TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  situation_refs JSONB NOT NULL,
  belief_refs JSONB NOT NULL,
  evidence_refs JSONB NOT NULL,
  memory_refs JSONB NOT NULL,
  goal_refs JSONB NOT NULL,
  task_refs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  assumptions JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  closed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_trace_id ON aion_decision_frames(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_actor_id ON aion_decision_frames(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_workspace_id ON aion_decision_frames(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_status ON aion_decision_frames(status);
CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_frame_type ON aion_decision_frames(frame_type);
CREATE INDEX IF NOT EXISTS ix_aion_decision_frames_created_at ON aion_decision_frames(created_at);

CREATE TABLE IF NOT EXISTS aion_decision_options (
  decision_option_id TEXT PRIMARY KEY,
  decision_frame_id TEXT NOT NULL REFERENCES aion_decision_frames(decision_frame_id),
  option_type TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  action_type TEXT NULL,
  target_type TEXT NULL,
  target_id TEXT NULL,
  expected_effects JSONB NOT NULL,
  required_permissions JSONB NOT NULL,
  required_approvals JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  reversibility TEXT NOT NULL,
  cost_estimate JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  archived_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_decision_options_frame ON aion_decision_options(decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_type ON aion_decision_options(option_type);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_status ON aion_decision_options(status);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_action_type ON aion_decision_options(action_type);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_target_type ON aion_decision_options(target_type);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_risk_level ON aion_decision_options(risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_reversibility ON aion_decision_options(reversibility);
CREATE INDEX IF NOT EXISTS ix_aion_decision_options_created_at ON aion_decision_options(created_at);

CREATE TABLE IF NOT EXISTS aion_utility_profiles (
  utility_profile_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  weights JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_utility_profiles_name ON aion_utility_profiles(name);
CREATE INDEX IF NOT EXISTS ix_aion_utility_profiles_status ON aion_utility_profiles(status);
CREATE INDEX IF NOT EXISTS ix_aion_utility_profiles_created_at ON aion_utility_profiles(created_at);

CREATE TABLE IF NOT EXISTS aion_option_evaluations (
  option_evaluation_id TEXT PRIMARY KEY,
  decision_frame_id TEXT NOT NULL REFERENCES aion_decision_frames(decision_frame_id),
  decision_option_id TEXT NOT NULL REFERENCES aion_decision_options(decision_option_id),
  utility_profile_id TEXT NULL,
  status TEXT NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  rank INTEGER NULL,
  factors JSONB NOT NULL,
  policy_decision_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  approval_request_id TEXT NULL,
  tradeoffs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  explanation TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_frame ON aion_option_evaluations(decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_option ON aion_option_evaluations(decision_option_id);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_profile ON aion_option_evaluations(utility_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_status ON aion_option_evaluations(status);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_score ON aion_option_evaluations(score);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_rank ON aion_option_evaluations(rank);
CREATE INDEX IF NOT EXISTS ix_aion_option_evaluations_created_at ON aion_option_evaluations(created_at);

CREATE TABLE IF NOT EXISTS aion_tradeoff_matrices (
  tradeoff_matrix_id TEXT PRIMARY KEY,
  decision_frame_id TEXT NOT NULL,
  utility_profile_id TEXT NULL,
  option_ids JSONB NOT NULL,
  criteria JSONB NOT NULL,
  scores JSONB NOT NULL,
  recommended_option_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_tradeoff_matrices_frame ON aion_tradeoff_matrices(decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_tradeoff_matrices_profile ON aion_tradeoff_matrices(utility_profile_id);
CREATE INDEX IF NOT EXISTS ix_aion_tradeoff_matrices_recommended ON aion_tradeoff_matrices(recommended_option_id);
CREATE INDEX IF NOT EXISTS ix_aion_tradeoff_matrices_created_at ON aion_tradeoff_matrices(created_at);

CREATE TABLE IF NOT EXISTS aion_counterfactual_runs (
  counterfactual_run_id TEXT PRIMARY KEY,
  decision_frame_id TEXT NOT NULL,
  decision_option_id TEXT NULL,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  input_state JSONB NOT NULL,
  assumptions JSONB NOT NULL,
  projected_changes JSONB NOT NULL,
  projected_risks JSONB NOT NULL,
  unknowns JSONB NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  result JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_frame ON aion_counterfactual_runs(decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_option ON aion_counterfactual_runs(decision_option_id);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_trace_id ON aion_counterfactual_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_status ON aion_counterfactual_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_mode ON aion_counterfactual_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_score ON aion_counterfactual_runs(score);
CREATE INDEX IF NOT EXISTS ix_aion_counterfactual_runs_created_at ON aion_counterfactual_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_decision_journal_records (
  decision_record_id TEXT PRIMARY KEY,
  decision_frame_id TEXT NOT NULL,
  selected_option_id TEXT NULL,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  decision_type TEXT NOT NULL,
  rationale TEXT NOT NULL,
  evaluation_refs JSONB NOT NULL,
  counterfactual_refs JSONB NOT NULL,
  approval_request_id TEXT NULL,
  policy_decision_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  outcome_ref TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  superseded_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_decision_records_frame ON aion_decision_journal_records(decision_frame_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_selected ON aion_decision_journal_records(selected_option_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_trace_id ON aion_decision_journal_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_actor_id ON aion_decision_journal_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_workspace_id ON aion_decision_journal_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_status ON aion_decision_journal_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_type ON aion_decision_journal_records(decision_type);
CREATE INDEX IF NOT EXISTS ix_aion_decision_records_created_at ON aion_decision_journal_records(created_at);
