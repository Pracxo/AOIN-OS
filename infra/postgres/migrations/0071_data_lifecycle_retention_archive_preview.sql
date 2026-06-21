CREATE TABLE IF NOT EXISTS aion_lifecycle_policies (
  lifecycle_policy_id TEXT PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  policy_type TEXT NOT NULL,
  resource_types JSONB NOT NULL,
  source_systems JSONB NOT NULL,
  retention_class TEXT NOT NULL,
  retention_days INTEGER NOT NULL,
  review_after_days INTEGER NULL,
  archive_after_days INTEGER NULL,
  purge_after_days INTEGER NULL,
  action_on_match TEXT NOT NULL,
  requires_backup BOOLEAN NOT NULL,
  requires_approval BOOLEAN NOT NULL,
  owner_scope JSONB NOT NULL,
  rule JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_name ON aion_lifecycle_policies(name);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_status ON aion_lifecycle_policies(status);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_type ON aion_lifecycle_policies(policy_type);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_class ON aion_lifecycle_policies(retention_class);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_action ON aion_lifecycle_policies(action_on_match);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_backup ON aion_lifecycle_policies(requires_backup);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_approval ON aion_lifecycle_policies(requires_approval);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_policies_created_at ON aion_lifecycle_policies(created_at);

CREATE TABLE IF NOT EXISTS aion_retention_classifications (
  classification_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  resource_uri TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  status TEXT NOT NULL,
  retention_class TEXT NOT NULL,
  lifecycle_state TEXT NOT NULL,
  sensitivity TEXT NOT NULL,
  policy_refs JSONB NOT NULL,
  reasons JSONB NOT NULL,
  retention_until TIMESTAMPTZ NULL,
  review_after TIMESTAMPTZ NULL,
  archive_after TIMESTAMPTZ NULL,
  purge_after TIMESTAMPTZ NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS ux_aion_retention_classifications_active_uri
  ON aion_retention_classifications(resource_uri)
  WHERE deleted_at IS NULL;
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_trace ON aion_retention_classifications(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_uri ON aion_retention_classifications(resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_type ON aion_retention_classifications(resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_resource_id ON aion_retention_classifications(resource_id);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_source ON aion_retention_classifications(source_system);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_status ON aion_retention_classifications(status);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_class ON aion_retention_classifications(retention_class);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_state ON aion_retention_classifications(lifecycle_state);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_sensitivity ON aion_retention_classifications(sensitivity);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_retention_until ON aion_retention_classifications(retention_until);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_review_after ON aion_retention_classifications(review_after);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_archive_after ON aion_retention_classifications(archive_after);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_purge_after ON aion_retention_classifications(purge_after);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_created_at ON aion_retention_classifications(created_at);
CREATE INDEX IF NOT EXISTS ix_aion_retention_classifications_deleted_at ON aion_retention_classifications(deleted_at);

CREATE TABLE IF NOT EXISTS aion_lifecycle_evaluation_runs (
  lifecycle_evaluation_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  mode TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_types JSONB NOT NULL,
  source_systems JSONB NOT NULL,
  policy_ids JSONB NOT NULL,
  resources_evaluated INTEGER NOT NULL,
  classifications_created INTEGER NOT NULL,
  archive_candidates_created INTEGER NOT NULL,
  redaction_candidates_created INTEGER NOT NULL,
  purge_previews_created INTEGER NOT NULL,
  reviews_created INTEGER NOT NULL,
  classifications JSONB NOT NULL,
  archive_candidates JSONB NOT NULL,
  redaction_candidates JSONB NOT NULL,
  purge_previews JSONB NOT NULL,
  review_records JSONB NOT NULL,
  warnings JSONB NOT NULL,
  failures JSONB NOT NULL,
  result JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  completed_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_trace ON aion_lifecycle_evaluation_runs(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_actor ON aion_lifecycle_evaluation_runs(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_workspace ON aion_lifecycle_evaluation_runs(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_status ON aion_lifecycle_evaluation_runs(status);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_mode ON aion_lifecycle_evaluation_runs(mode);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_evaluated ON aion_lifecycle_evaluation_runs(resources_evaluated);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_classifications_created ON aion_lifecycle_evaluation_runs(classifications_created);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_archive_created ON aion_lifecycle_evaluation_runs(archive_candidates_created);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_redaction_created ON aion_lifecycle_evaluation_runs(redaction_candidates_created);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_purge_created ON aion_lifecycle_evaluation_runs(purge_previews_created);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_reviews_created ON aion_lifecycle_evaluation_runs(reviews_created);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_runs_created_at ON aion_lifecycle_evaluation_runs(created_at);

CREATE TABLE IF NOT EXISTS aion_archive_candidates (
  archive_candidate_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  resource_uri TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  reason TEXT NOT NULL,
  lifecycle_policy_id TEXT NULL,
  classification_id TEXT NULL,
  backup_required BOOLEAN NOT NULL,
  backup_verified BOOLEAN NOT NULL,
  action_proposal_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ NULL,
  dismissed_at TIMESTAMPTZ NULL,
  converted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_trace ON aion_archive_candidates(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_uri ON aion_archive_candidates(resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_type ON aion_archive_candidates(resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_resource_id ON aion_archive_candidates(resource_id);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_source ON aion_archive_candidates(source_system);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_status ON aion_archive_candidates(status);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_severity ON aion_archive_candidates(severity);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_policy ON aion_archive_candidates(lifecycle_policy_id);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_backup_required ON aion_archive_candidates(backup_required);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_backup_verified ON aion_archive_candidates(backup_verified);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_action_proposal ON aion_archive_candidates(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_archive_candidates_created_at ON aion_archive_candidates(created_at);

CREATE TABLE IF NOT EXISTS aion_redaction_candidates (
  redaction_candidate_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  resource_uri TEXT NOT NULL,
  resource_type TEXT NOT NULL,
  resource_id TEXT NOT NULL,
  source_system TEXT NOT NULL,
  status TEXT NOT NULL,
  severity TEXT NOT NULL,
  reason TEXT NOT NULL,
  sensitive_paths JSONB NOT NULL,
  suggested_redaction_mode TEXT NOT NULL,
  lifecycle_policy_id TEXT NULL,
  classification_id TEXT NULL,
  action_proposal_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  reviewed_at TIMESTAMPTZ NULL,
  dismissed_at TIMESTAMPTZ NULL,
  converted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_trace ON aion_redaction_candidates(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_uri ON aion_redaction_candidates(resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_type ON aion_redaction_candidates(resource_type);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_resource_id ON aion_redaction_candidates(resource_id);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_source ON aion_redaction_candidates(source_system);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_status ON aion_redaction_candidates(status);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_severity ON aion_redaction_candidates(severity);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_mode ON aion_redaction_candidates(suggested_redaction_mode);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_policy ON aion_redaction_candidates(lifecycle_policy_id);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_action_proposal ON aion_redaction_candidates(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_redaction_candidates_created_at ON aion_redaction_candidates(created_at);

CREATE TABLE IF NOT EXISTS aion_purge_previews (
  purge_preview_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_uris JSONB NOT NULL,
  resource_count INTEGER NOT NULL,
  blocked_count INTEGER NOT NULL,
  allowed_count INTEGER NOT NULL,
  blockers JSONB NOT NULL,
  warnings JSONB NOT NULL,
  estimated_impact JSONB NOT NULL,
  requires_backup BOOLEAN NOT NULL,
  backup_verified BOOLEAN NOT NULL,
  hard_delete_allowed BOOLEAN NOT NULL,
  result JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_trace ON aion_purge_previews(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_status ON aion_purge_previews(status);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_resource_count ON aion_purge_previews(resource_count);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_blocked_count ON aion_purge_previews(blocked_count);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_allowed_count ON aion_purge_previews(allowed_count);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_backup_required ON aion_purge_previews(requires_backup);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_backup_verified ON aion_purge_previews(backup_verified);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_hard_delete ON aion_purge_previews(hard_delete_allowed);
CREATE INDEX IF NOT EXISTS ix_aion_purge_previews_created_at ON aion_purge_previews(created_at);

CREATE TABLE IF NOT EXISTS aion_lifecycle_review_records (
  lifecycle_review_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  resource_uri TEXT NULL,
  candidate_type TEXT NOT NULL,
  candidate_id TEXT NULL,
  status TEXT NOT NULL,
  decision TEXT NOT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  reason TEXT NOT NULL,
  policy_decision_id TEXT NULL,
  approval_request_id TEXT NULL,
  action_proposal_id TEXT NULL,
  owner_scope JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_trace ON aion_lifecycle_review_records(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_uri ON aion_lifecycle_review_records(resource_uri);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_candidate_type ON aion_lifecycle_review_records(candidate_type);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_candidate_id ON aion_lifecycle_review_records(candidate_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_status ON aion_lifecycle_review_records(status);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_decision ON aion_lifecycle_review_records(decision);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_actor ON aion_lifecycle_review_records(actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_workspace ON aion_lifecycle_review_records(workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_action_proposal ON aion_lifecycle_review_records(action_proposal_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reviews_created_at ON aion_lifecycle_review_records(created_at);

CREATE TABLE IF NOT EXISTS aion_lifecycle_reports (
  lifecycle_report_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  status TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  resource_count INTEGER NOT NULL,
  classified_count INTEGER NOT NULL,
  archive_candidate_count INTEGER NOT NULL,
  redaction_candidate_count INTEGER NOT NULL,
  purge_preview_count INTEGER NOT NULL,
  overdue_review_count INTEGER NOT NULL,
  sensitive_resource_count INTEGER NOT NULL,
  findings JSONB NOT NULL,
  recommendations JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_trace ON aion_lifecycle_reports(trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_status ON aion_lifecycle_reports(status);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_resource_count ON aion_lifecycle_reports(resource_count);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_classified_count ON aion_lifecycle_reports(classified_count);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_archive_count ON aion_lifecycle_reports(archive_candidate_count);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_redaction_count ON aion_lifecycle_reports(redaction_candidate_count);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_overdue_count ON aion_lifecycle_reports(overdue_review_count);
CREATE INDEX IF NOT EXISTS ix_aion_lifecycle_reports_created_at ON aion_lifecycle_reports(created_at);
