CREATE TABLE IF NOT EXISTS aion_prompt_templates (
  prompt_template_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  template_type TEXT NOT NULL,
  version TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  sections JSONB NOT NULL,
  required_inputs JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL,
  CONSTRAINT uq_aion_prompt_templates_name_version UNIQUE (name, version)
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_templates_name ON aion_prompt_templates (name);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_templates_status ON aion_prompt_templates (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_templates_template_type ON aion_prompt_templates (template_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_templates_version ON aion_prompt_templates (version);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_templates_created_at ON aion_prompt_templates (created_at);

CREATE TABLE IF NOT EXISTS aion_prompt_fragments (
  prompt_fragment_id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT NOT NULL,
  fragment_type TEXT NOT NULL,
  content TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  owner_scope JSONB NOT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  disabled_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_fragments_name ON aion_prompt_fragments (name);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_fragments_status ON aion_prompt_fragments (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_fragments_fragment_type ON aion_prompt_fragments (fragment_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_fragments_content_hash ON aion_prompt_fragments (content_hash);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_fragments_created_at ON aion_prompt_fragments (created_at);

CREATE TABLE IF NOT EXISTS aion_prompt_packets (
  prompt_packet_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  actor_id TEXT NULL,
  workspace_id TEXT NULL,
  status TEXT NOT NULL,
  packet_type TEXT NOT NULL,
  prompt_template_id TEXT NULL,
  target_model_route TEXT NULL,
  owner_scope JSONB NOT NULL,
  input_refs JSONB NOT NULL,
  section_manifests JSONB NOT NULL,
  rendered_hash TEXT NOT NULL,
  redacted_preview TEXT NULL,
  token_estimate INTEGER NOT NULL,
  char_count INTEGER NOT NULL,
  boundary_check_id TEXT NULL,
  grounding_verification_id TEXT NULL,
  instruction_resolution_id TEXT NULL,
  constraints JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_trace_id ON aion_prompt_packets (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_actor_id ON aion_prompt_packets (actor_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_workspace_id ON aion_prompt_packets (workspace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_status ON aion_prompt_packets (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_packet_type ON aion_prompt_packets (packet_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_prompt_template_id ON aion_prompt_packets (prompt_template_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_target_model_route ON aion_prompt_packets (target_model_route);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_rendered_hash ON aion_prompt_packets (rendered_hash);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_boundary_check_id ON aion_prompt_packets (boundary_check_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_grounding_verification_id ON aion_prompt_packets (grounding_verification_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_instruction_resolution_id ON aion_prompt_packets (instruction_resolution_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_created_at ON aion_prompt_packets (created_at);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_packets_deleted_at ON aion_prompt_packets (deleted_at);

CREATE TABLE IF NOT EXISTS aion_prompt_boundary_checks (
  boundary_check_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  prompt_packet_id TEXT NULL,
  status TEXT NOT NULL,
  safe BOOLEAN NOT NULL,
  injection_findings JSONB NOT NULL,
  blocked_sections JSONB NOT NULL,
  warnings JSONB NOT NULL,
  constraints JSONB NOT NULL,
  score DOUBLE PRECISION NOT NULL,
  metadata JSONB NOT NULL,
  created_by TEXT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_trace_id ON aion_prompt_boundary_checks (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_prompt_packet_id ON aion_prompt_boundary_checks (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_status ON aion_prompt_boundary_checks (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_safe ON aion_prompt_boundary_checks (safe);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_score ON aion_prompt_boundary_checks (score);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_boundary_checks_created_at ON aion_prompt_boundary_checks (created_at);

CREATE TABLE IF NOT EXISTS aion_prompt_injection_findings (
  injection_finding_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  prompt_packet_id TEXT NULL,
  source_type TEXT NOT NULL,
  source_id TEXT NULL,
  finding_type TEXT NOT NULL,
  severity TEXT NOT NULL,
  status TEXT NOT NULL,
  matched_text_redacted TEXT NOT NULL,
  reason TEXT NOT NULL,
  recommended_action TEXT NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  resolved_at TIMESTAMPTZ NULL
);

CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_trace_id ON aion_prompt_injection_findings (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_prompt_packet_id ON aion_prompt_injection_findings (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_source_type ON aion_prompt_injection_findings (source_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_source_id ON aion_prompt_injection_findings (source_id);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_finding_type ON aion_prompt_injection_findings (finding_type);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_severity ON aion_prompt_injection_findings (severity);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_status ON aion_prompt_injection_findings (status);
CREATE INDEX IF NOT EXISTS ix_aion_prompt_injection_findings_created_at ON aion_prompt_injection_findings (created_at);

CREATE TABLE IF NOT EXISTS aion_model_input_manifests (
  model_input_manifest_id TEXT PRIMARY KEY,
  trace_id TEXT NULL,
  prompt_packet_id TEXT NOT NULL,
  model_route TEXT NULL,
  provider_type TEXT NULL,
  status TEXT NOT NULL,
  input_hash TEXT NOT NULL,
  section_count INTEGER NOT NULL,
  token_estimate INTEGER NOT NULL,
  context_budget JSONB NOT NULL,
  grounding_refs JSONB NOT NULL,
  instruction_refs JSONB NOT NULL,
  safety_refs JSONB NOT NULL,
  metadata JSONB NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_trace_id ON aion_model_input_manifests (trace_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_prompt_packet_id ON aion_model_input_manifests (prompt_packet_id);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_model_route ON aion_model_input_manifests (model_route);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_provider_type ON aion_model_input_manifests (provider_type);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_status ON aion_model_input_manifests (status);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_input_hash ON aion_model_input_manifests (input_hash);
CREATE INDEX IF NOT EXISTS ix_aion_model_input_manifests_created_at ON aion_model_input_manifests (created_at);
