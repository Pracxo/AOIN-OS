CREATE TABLE IF NOT EXISTS aion_golden_path_scenarios (
  golden_path_scenario_id TEXT PRIMARY KEY,
  scenario_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  scenario_type TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  required_services JSONB NOT NULL,
  steps JSONB NOT NULL,
  assertions JSONB NOT NULL,
  tags JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_scenarios_key
  ON aion_golden_path_scenarios (scenario_key);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_scenarios_status
  ON aion_golden_path_scenarios (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_scenarios_type
  ON aion_golden_path_scenarios (scenario_type);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_scenarios_created_at
  ON aion_golden_path_scenarios (created_at);

CREATE TABLE IF NOT EXISTS aion_golden_path_fixture_packs (
  fixture_pack_id TEXT PRIMARY KEY,
  fixture_pack_key TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  workspace_id TEXT NULL,
  fixtures JSONB NOT NULL,
  seeded_resource_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_fixture_packs_key
  ON aion_golden_path_fixture_packs (fixture_pack_key);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_fixture_packs_status
  ON aion_golden_path_fixture_packs (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_fixture_packs_workspace
  ON aion_golden_path_fixture_packs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_fixture_packs_created_at
  ON aion_golden_path_fixture_packs (created_at);

CREATE TABLE IF NOT EXISTS aion_golden_path_runs (
  golden_path_run_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  scenario_ids JSONB NOT NULL,
  fixture_pack_ids JSONB NOT NULL,
  started_at TIMESTAMPTZ NOT NULL,
  completed_at TIMESTAMPTZ NULL,
  passed_count INTEGER NOT NULL,
  failed_count INTEGER NOT NULL,
  warning_count INTEGER NOT NULL,
  skipped_count INTEGER NOT NULL,
  blocked_count INTEGER NOT NULL,
  step_result_ids JSONB NOT NULL,
  assertion_result_ids JSONB NOT NULL,
  report_id TEXT NULL,
  warnings JSONB NOT NULL,
  failures JSONB NOT NULL,
  result JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_trace
  ON aion_golden_path_runs (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_actor
  ON aion_golden_path_runs (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_workspace
  ON aion_golden_path_runs (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_status
  ON aion_golden_path_runs (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_mode
  ON aion_golden_path_runs (mode);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_started_at
  ON aion_golden_path_runs (started_at);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_completed_at
  ON aion_golden_path_runs (completed_at);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_runs_created_at
  ON aion_golden_path_runs (created_at);

CREATE TABLE IF NOT EXISTS aion_golden_path_step_results (
  step_result_id TEXT PRIMARY KEY,
  golden_path_run_id TEXT NOT NULL REFERENCES aion_golden_path_runs(golden_path_run_id),
  golden_path_scenario_id TEXT NOT NULL REFERENCES aion_golden_path_scenarios(golden_path_scenario_id),
  trace_id TEXT NULL,
  step_key TEXT NOT NULL,
  step_order INTEGER NOT NULL,
  status TEXT NOT NULL,
  service_name TEXT NOT NULL,
  action_name TEXT NOT NULL,
  input_summary JSONB NOT NULL,
  output_summary JSONB NOT NULL,
  resource_refs JSONB NOT NULL,
  duration_ms INTEGER NULL,
  error JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_run
  ON aion_golden_path_step_results (golden_path_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_scenario
  ON aion_golden_path_step_results (golden_path_scenario_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_key
  ON aion_golden_path_step_results (step_key);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_order
  ON aion_golden_path_step_results (step_order);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_status
  ON aion_golden_path_step_results (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_service
  ON aion_golden_path_step_results (service_name);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_action
  ON aion_golden_path_step_results (action_name);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_steps_created_at
  ON aion_golden_path_step_results (created_at);

CREATE TABLE IF NOT EXISTS aion_golden_path_assertion_results (
  assertion_result_id TEXT PRIMARY KEY,
  golden_path_run_id TEXT NOT NULL REFERENCES aion_golden_path_runs(golden_path_run_id),
  golden_path_scenario_id TEXT NOT NULL REFERENCES aion_golden_path_scenarios(golden_path_scenario_id),
  step_result_id TEXT NULL,
  trace_id TEXT NULL,
  assertion_key TEXT NOT NULL,
  assertion_type TEXT NOT NULL,
  status TEXT NOT NULL,
  expected JSONB NOT NULL,
  actual JSONB NOT NULL,
  message TEXT NOT NULL,
  severity TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_run
  ON aion_golden_path_assertion_results (golden_path_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_scenario
  ON aion_golden_path_assertion_results (golden_path_scenario_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_step
  ON aion_golden_path_assertion_results (step_result_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_key
  ON aion_golden_path_assertion_results (assertion_key);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_type
  ON aion_golden_path_assertion_results (assertion_type);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_status
  ON aion_golden_path_assertion_results (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_severity
  ON aion_golden_path_assertion_results (severity);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_assertions_created_at
  ON aion_golden_path_assertion_results (created_at);

CREATE TABLE IF NOT EXISTS aion_golden_path_reports (
  golden_path_report_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  golden_path_run_id TEXT NULL,
  scenario_count INTEGER NOT NULL,
  passed_count INTEGER NOT NULL,
  failed_count INTEGER NOT NULL,
  warning_count INTEGER NOT NULL,
  blocked_count INTEGER NOT NULL,
  readiness_score DOUBLE PRECISION NOT NULL,
  release_candidate_ready BOOLEAN NOT NULL,
  findings JSONB NOT NULL,
  recommendations JSONB NOT NULL,
  report JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_trace
  ON aion_golden_path_reports (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_status
  ON aion_golden_path_reports (status);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_run
  ON aion_golden_path_reports (golden_path_run_id);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_score
  ON aion_golden_path_reports (readiness_score);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_ready
  ON aion_golden_path_reports (release_candidate_ready);
CREATE INDEX IF NOT EXISTS ix_aion_golden_path_reports_created_at
  ON aion_golden_path_reports (created_at);
