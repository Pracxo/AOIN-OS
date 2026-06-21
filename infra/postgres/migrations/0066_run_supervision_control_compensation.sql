CREATE TABLE IF NOT EXISTS aion_run_supervision_records (
  run_supervision_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  target_system TEXT NOT NULL,
  target_run_id TEXT NULL,
  status TEXT NOT NULL,
  run_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  current_status TEXT NOT NULL,
  previous_status TEXT NULL,
  timeout_policy_id TEXT NULL,
  deadline_at TIMESTAMPTZ NULL,
  last_sample_id TEXT NULL,
  last_seen_at TIMESTAMPTZ NULL,
  stalled BOOLEAN NOT NULL,
  cancellable BOOLEAN NOT NULL,
  pausable BOOLEAN NOT NULL,
  resumable BOOLEAN NOT NULL,
  compensation_available BOOLEAN NOT NULL,
  outcome_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL,
  archived_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_trace_id ON aion_run_supervision_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_actor_id ON aion_run_supervision_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_workspace_id ON aion_run_supervision_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_source_type ON aion_run_supervision_records(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_source_id ON aion_run_supervision_records(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_target_system ON aion_run_supervision_records(target_system);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_target_run_id ON aion_run_supervision_records(target_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_status ON aion_run_supervision_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_run_type ON aion_run_supervision_records(run_type);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_current_status ON aion_run_supervision_records(current_status);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_stalled ON aion_run_supervision_records(stalled);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_deadline_at ON aion_run_supervision_records(deadline_at);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_last_seen_at ON aion_run_supervision_records(last_seen_at);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_created_at ON aion_run_supervision_records(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervisions_deleted_at ON aion_run_supervision_records(deleted_at);

CREATE TABLE IF NOT EXISTS aion_run_status_samples (
  run_status_sample_id TEXT PRIMARY KEY,
  run_supervision_id TEXT NOT NULL REFERENCES aion_run_supervision_records(run_supervision_id),
  trace_id TEXT NULL,
  target_system TEXT NOT NULL,
  target_run_id TEXT NULL,
  observed_status TEXT NOT NULL,
  raw_status JSONB NOT NULL,
  progress JSONB NOT NULL,
  error JSONB NOT NULL,
  latency_ms INTEGER NULL,
  metadata JSONB NOT NULL,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_run_samples_run_supervision_id ON aion_run_status_samples(run_supervision_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_samples_trace_id ON aion_run_status_samples(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_samples_target_system ON aion_run_status_samples(target_system);
CREATE INDEX IF NOT EXISTS ix_aion_run_samples_target_run_id ON aion_run_status_samples(target_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_samples_observed_status ON aion_run_status_samples(observed_status);
CREATE INDEX IF NOT EXISTS ix_aion_run_samples_observed_at ON aion_run_status_samples(observed_at);

CREATE TABLE IF NOT EXISTS aion_run_control_requests (
  run_control_request_id TEXT PRIMARY KEY,
  run_supervision_id TEXT NOT NULL REFERENCES aion_run_supervision_records(run_supervision_id),
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  control_type TEXT NOT NULL,
  status TEXT NOT NULL,
  reason TEXT NOT NULL,
  requested_mode TEXT NOT NULL,
  target_system TEXT NOT NULL,
  target_run_id TEXT NULL,
  policy_decision_id TEXT NULL,
  risk_assessment_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  approval_request_id TEXT NULL,
  blocker_refs JSONB NOT NULL,
  result JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_run_controls_run_supervision_id ON aion_run_control_requests(run_supervision_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_trace_id ON aion_run_control_requests(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_actor_id ON aion_run_control_requests(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_workspace_id ON aion_run_control_requests(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_control_type ON aion_run_control_requests(control_type);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_status ON aion_run_control_requests(status);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_requested_mode ON aion_run_control_requests(requested_mode);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_target_system ON aion_run_control_requests(target_system);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_target_run_id ON aion_run_control_requests(target_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_controls_created_at ON aion_run_control_requests(created_at);

CREATE TABLE IF NOT EXISTS aion_run_timeout_policies (
  timeout_policy_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  target_system TEXT NOT NULL,
  run_type TEXT NOT NULL,
  timeout_seconds INTEGER NOT NULL,
  stall_after_seconds INTEGER NOT NULL,
  max_status_age_seconds INTEGER NOT NULL,
  severity TEXT NOT NULL,
  action_on_timeout TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_name ON aion_run_timeout_policies(name);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_status ON aion_run_timeout_policies(status);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_target_system ON aion_run_timeout_policies(target_system);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_run_type ON aion_run_timeout_policies(run_type);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_severity ON aion_run_timeout_policies(severity);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_action_on_timeout ON aion_run_timeout_policies(action_on_timeout);
CREATE INDEX IF NOT EXISTS ix_aion_run_timeout_policies_created_at ON aion_run_timeout_policies(created_at);

CREATE TABLE IF NOT EXISTS aion_compensation_plans (
  compensation_plan_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  run_supervision_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NOT NULL,
  status TEXT NOT NULL,
  plan_type TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  trigger_reason TEXT NOT NULL,
  target_refs JSONB NOT NULL,
  step_ids JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  approval_request_id TEXT NULL,
  policy_decision_id TEXT NULL,
  autonomy_decision_id TEXT NULL,
  executable BOOLEAN NOT NULL,
  execution_allowed BOOLEAN NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  approved_at TIMESTAMPTZ NULL,
  archived_at TIMESTAMPTZ NULL,
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_trace_id ON aion_compensation_plans(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_run_supervision_id ON aion_compensation_plans(run_supervision_id);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_source_type ON aion_compensation_plans(source_type);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_source_id ON aion_compensation_plans(source_id);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_status ON aion_compensation_plans(status);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_plan_type ON aion_compensation_plans(plan_type);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_risk_level ON aion_compensation_plans(risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_executable ON aion_compensation_plans(executable);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_execution_allowed ON aion_compensation_plans(execution_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_created_at ON aion_compensation_plans(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_plans_deleted_at ON aion_compensation_plans(deleted_at);

CREATE TABLE IF NOT EXISTS aion_compensation_steps (
  compensation_step_id TEXT PRIMARY KEY,
  compensation_plan_id TEXT NOT NULL REFERENCES aion_compensation_plans(compensation_plan_id),
  step_order INTEGER NOT NULL,
  step_type TEXT NOT NULL,
  status TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  proposed_action_type TEXT NULL,
  proposed_target_system TEXT NULL,
  proposed_payload JSONB NOT NULL,
  expected_effects JSONB NOT NULL,
  risk_level TEXT NOT NULL,
  requires_approval BOOLEAN NOT NULL,
  action_proposal_id TEXT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_plan_id ON aion_compensation_steps(compensation_plan_id);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_step_order ON aion_compensation_steps(step_order);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_step_type ON aion_compensation_steps(step_type);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_status ON aion_compensation_steps(status);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_proposed_action_type ON aion_compensation_steps(proposed_action_type);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_proposed_target_system ON aion_compensation_steps(proposed_target_system);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_risk_level ON aion_compensation_steps(risk_level);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_requires_approval ON aion_compensation_steps(requires_approval);
CREATE INDEX IF NOT EXISTS ix_aion_compensation_steps_created_at ON aion_compensation_steps(created_at);

CREATE TABLE IF NOT EXISTS aion_run_supervision_reports (
  supervision_report_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  target_systems JSONB NOT NULL,
  run_count INTEGER NOT NULL,
  active_count INTEGER NOT NULL,
  completed_count INTEGER NOT NULL,
  failed_count INTEGER NOT NULL,
  stalled_count INTEGER NOT NULL,
  timeout_count INTEGER NOT NULL,
  control_request_count INTEGER NOT NULL,
  compensation_plan_count INTEGER NOT NULL,
  findings JSONB NOT NULL,
  recommendations JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_trace_id ON aion_run_supervision_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_status ON aion_run_supervision_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_run_count ON aion_run_supervision_reports(run_count);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_stalled_count ON aion_run_supervision_reports(stalled_count);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_timeout_count ON aion_run_supervision_reports(timeout_count);
CREATE INDEX IF NOT EXISTS ix_aion_run_supervision_reports_created_at ON aion_run_supervision_reports(created_at);
