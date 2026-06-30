# AION Python SDK

The Python SDK is the supported local developer client for AION Brain. It is a
separate package under `packages/aion-sdk-python` and communicates with AION
Brain through public HTTP APIs only.

The SDK owns:

- Client configuration from environment variables
- Development identity and trace headers
- Typed error mapping for `AIONErrorResponse`
- Resource wrappers for public Brain APIs
- A small forward-compatible model layer

The SDK does not own:

- Brain server internals
- Database access
- Provider SDK calls
- Production authentication
- Domain-specific modules

## Client Example

```python
from aion_sdk import AIONClient

client = AIONClient()
print(client.health.ready())
print(client.kernel.contracts())
```

## Model Outputs Resource

`client.model_outputs` supports:

- `create(payload)`
- `get(model_output_id, scope)`
- `query(payload)`
- `delete(model_output_id, reason, actor_id=None)`
- `govern(model_output_id, payload)`
- `get_governance(output_governance_id)`
- `segments(model_output_id, scope)`
- `validate_structured(model_output_id, scope, schema_name=None)`
- `response_candidates(scope, status=None, trace_id=None, limit=100)`
- `promote_candidate(response_candidate_id, approval_present=False, reason="operator_requested")`
- `tool_intents(scope, status=None, trace_id=None, limit=100)`
- `reject_tool_intent(tool_intent_id, reason, actor_id=None)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, access
databases, execute model-suggested tools, or expose raw provider payloads.

## Action Proposals Resource

`client.action_proposals` supports:

- `create(payload)`
- `get(action_proposal_id, scope)`
- `query(payload)`
- `archive(action_proposal_id, reason, actor_id=None)`
- `delete(action_proposal_id, reason, actor_id=None)`
- `review_tool_intent(tool_intent_id, payload)`
- `list_tool_intent_reviews(tool_intent_id=None, status=None, limit=100)`
- `review(action_proposal_id, payload)`
- `list_reviews(action_proposal_id)`
- `list_blockers(action_proposal_id=None, status=None, severity=None, limit=100)`
- `resolve_blocker(action_blocker_id, reason, actor_id=None)`
- `handoff(payload)`
- `get_handoff(execution_handoff_id, scope)`
- `list_handoffs(action_proposal_id=None, status=None, target_system=None, limit=100)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, dispatch
commands, run workflows, invoke capabilities, call MCP tools, execute sandbox
runs, approve actions, or call external systems. Handoff payloads default to
dry-run.

## Error Handling

AION public API errors map to SDK exceptions:

- `AIONValidationError`
- `AIONPolicyDeniedError`
- `AIONAutonomyDeniedError`
- `AIONApprovalRequiredError`
- `AIONConflictError`
- `AIONNotFoundError`
- `AIONDependencyUnavailableError`

Unknown AION errors remain `AIONAPIError`. Non-AION HTTP failures become
`AIONHTTPError`.

## Headers

The SDK builds AION development headers:

- `X-AION-Actor-ID`
- `X-AION-Workspace-ID`
- `X-AION-Roles`
- `X-AION-Permissions`
- `X-AION-Security-Scope`
- `X-AION-Trace-ID`
- `X-AION-Correlation-ID`
- `Idempotency-Key`
- `User-Agent`

It intentionally strips `Authorization` from helper-built headers.

## Modules Resource

`client.modules` supports:

- `submit_package(payload)`
- `list_packages(status=None, module_id=None)`
- `get_package(module_package_id)`
- `certify(module_package_id, payload)`
- `scaffold(payload)`
- `compatibility(module_package_id)`
- `run_contract_tests(module_package_id, dry_run=True)`

The SDK does not execute module code. It calls public Module Developer Kit HTTP
APIs only.

## Sandbox Resource

`client.sandbox` supports:

- `create_profile(payload)`
- `list_profiles(scope, status=None)`
- `validate_profile(sandbox_profile_id, scope)`
- `run(payload)`
- `create_secret_ref(payload)`
- `list_secret_refs(scope, status=None)`
- `create_connector(payload)`
- `list_connectors(scope, status=None, connector_type=None)`
- `validate_connector(connector_id, scope)`

The SDK sends metadata-only requests to the public Brain API. It does not
import `aion_brain`, access databases, execute containers, accept raw secrets,
or call external connector systems.

## Connector Runtime Resource

`client.connector_runtime` supports disabled connector prototype evidence:

- `status(scope)`
- `validate_manifest(payload)`
- `egress_preview(payload)`
- `ingress_preview(payload)`
- `audit(payload)`

The resource calls public Brain APIs only. It does not import `aion_brain`,
add connector/provider SDKs, store credentials, store tokens, activate
connectors, or call external systems.

## Connector Simulator Resource

`client.connector_simulator` supports synthetic dry-run evidence:

- `simulate(payload)`
- `replay(payload)`
- `policy_readiness(payload)`
- `status(scope)`
- `query(payload)`

The resource calls public Brain APIs only. It does not import `aion_brain`, add
connector/provider SDKs, execute connectors, store credentials, store tokens,
activate runtime, register routes, or call external systems.

## Scenarios Resource

`client.scenarios` supports the end-to-end validation harness:

- `create(payload)`
- `list(status=None, scenario_type=None, tags=None)`
- `get(scenario_id, scope)`
- `run(payload)`
- `get_run(scenario_run_id, scope)`
- `runs(scope, status=None, scenario_type=None, limit=50)`
- `seed_defaults(scope, dry_run=True)`
- `list_fixtures(scope, fixture_type=None)`
- `load_fixture(payload)`
- `run_release_baseline(payload)`
- `get_release_baseline(release_baseline_id)`
- `list_release_baselines(scope, version=None, status=None, limit=50)`

The SDK calls public Brain APIs only. Scenario runs and release baselines are
dry-run by default and must not require external services, optional adapters,
full autonomy, external tool execution, or domain-specific scenario packs.

## Versioning Resource

`client.versioning` supports:

- `create_manifest(payload)`
- `get_manifest(version)`
- `list_manifests(status=None, limit=50)`
- `freeze_manifest(version, payload)`
- `seed_features(scope, dry_run=True)`
- `list_features(scope, status=None, category=None)`
- `create_feature(payload)`
- `deprecate_feature(feature_key, scope, reason)`
- `generate_compatibility(version, scope)`
- `get_compatibility(version)`
- `generate_migration_baseline(version, scope)`
- `generate_release_artifacts(version, scope, created_by=None)`
- `sdk_compatibility(scope)`
- `run_freeze_gate(payload)`
- `get_freeze_gate(freeze_gate_id)`
- `list_freeze_gates(scope, version=None, status=None)`

The SDK uses public HTTP endpoints only and does not import Brain API internals
or optional adapter clients.

## Release Resource

`client.release` supports:

- `create_package(payload)`
- `get_package(release_package_id, scope=None)`
- `list_packages(scope, version=None, status=None)`
- `validate_package(release_package_id, scope)`
- `handoff(release_package_id, scope)`

The SDK calls public release package APIs only. It does not read local files,
compute checksums, upload artifacts, call registries, or import Brain API
internals.

## Bootstrap Resource

`client.bootstrap` supports:

- `seed_profiles(scope, dry_run=True)`
- `list_profiles(scope, status=None, profile_type=None, limit=100)`
- `seed_bundles(scope, dry_run=True)`
- `list_seed_bundles(scope, status=None, bundle_type=None, limit=100)`
- `seed(payload)`
- `doctor(payload)`
- `run(payload)`
- `list_runs(scope, status=None, profile_key=None, limit=50)`
- `get_run(bootstrap_run_id, scope)`
- `list_findings(scope, status=None, severity=None, category=None, limit=100)`
- `dismiss_finding(setup_finding_id, scope, reason="dismissed")`
- `list_reports(scope, status=None, limit=50)`
- `get_report(setup_report_id, scope)`

The SDK calls public Brain APIs only. Bootstrap helpers do not install
packages, create credentials, mutate source code, call external systems, enable
full autonomy, or access server internals.

## Dialogue and Responses Resources

`client.dialogue` supports:

- `create_session(payload)`
- `get_session(dialogue_session_id, scope)`
- `list_sessions(scope, status=None, session_type=None, limit=50)`
- `close_session(dialogue_session_id, reason)`
- `create_message(payload)`
- `list_messages(dialogue_session_id, scope, limit=100)`
- `turn(payload)`
- `pending_clarifications(scope, dialogue_session_id=None)`
- `answer_clarification(clarification_id, answer)`
- `feedback(payload)`

`client.responses` supports:

- `compose(payload)`
- `get(response_id)`
- `verify(response_id)`
- `deliver_local(response_id)`
- `deliveries(response_id)`

The SDK uses public Brain HTTP APIs only. It does not import `aion_brain`,
database drivers, provider SDKs, frontend code, or external delivery clients.
Dialogue turns remain backend-only and do not execute controlled actions.

## Beliefs Resource

`client.beliefs` supports:

- `create_claim(payload)`
- `get_claim(claim_id, scope)`
- `query(payload)`
- `revise_claim(claim_id, payload)`
- `create_support(payload)`
- `list_supports(claim_id)`
- `list_contradictions(scope, status=None, severity=None, limit=100)`
- `resolve_contradiction(contradiction_id, reason)`
- `extract(payload)`
- `run_truth_maintenance(payload)`
- `get_truth_maintenance(truth_run_id)`

The SDK treats belief state as public Brain HTTP contracts only. It does not
import `aion_brain`, database clients, model providers, fact-checking services,
or visual frontend libraries.

## Concepts and Entities Resources

`client.concepts` supports:

- `create(payload)`
- `list(scope, query=None, concept_type=None, status="active", limit=100)`
- `list_concepts(scope, query=None, concept_type=None, status="active", limit=100)`
- `get(concept_id, scope)`
- `archive(concept_id, reason, scope)`

`client.entities` supports:

- `create(payload)`
- `get(entity_id, scope)`
- `query(payload)`
- `archive(entity_id, reason, scope)`
- `delete(entity_id, reason, scope)`
- `add_alias(payload, scope)`
- `list_aliases(entity_id, scope)`
- `create_mention(payload)`
- `list_mentions(entity_id, scope, limit=100)`
- `extract_mentions(payload)`
- `resolve(payload)`
- `get_resolution_run(resolution_run_id, scope)`
- `create_reference(payload, scope)`
- `list_references(scope, **filters)`
- `propose_merge(payload, scope)`
- `approve_merge(proposal_id, reason_or_payload, scope)`
- `reject_merge(proposal_id, reason_or_payload, scope)`
- `propose_split(payload, scope)`
- `approve_split(proposal_id, reason_or_payload, scope)`
- `reject_split(proposal_id, reason_or_payload, scope)`

The SDK uses public Brain HTTP APIs only. It does not import `aion_brain`,
external NLP libraries, model providers, image recognition services, or domain
ontology packages.
## DecisionsResource

`client.decisions` exposes decision frames, options, utility profiles,
evaluation, recommendation, counterfactual dry-runs, and decision journal
records. SDK decision helpers call public Brain APIs only and never execute a
selected option.

## Outcomes Resource

`client.outcomes` supports:

- `create(payload)`
- `get(outcome_id)`
- `query(payload)`
- `close(outcome_id, reason)`
- `delete(outcome_id, reason)`
- `create_expected_effect(payload)`
- `get_expected_effect(expected_effect_id)`
- `create_observed_effect(payload)`
- `get_observed_effect(observed_effect_id)`
- `verify(payload)`
- `get_verification(verification_run_id)`
- `create_attribution(payload)`
- `list_attributions(**filters)`
- `create_feedback(payload)`
- `list_feedback(**filters)`
- `resolve_feedback(feedback_id, resolution)`
- `learning_bridge(outcome_id, dry_run=True)`

The SDK calls public Brain HTTP APIs only. It does not import `aion_brain`,
database clients, provider SDKs, frontend code, or external observability
clients. Outcome learning bridge calls remain review-only.

## Learning Resource

`client.learning` supports:

- `create_experience(payload)`
- `get_experience(experience_id, scope)`
- `query(payload)`
- `archive_experience(experience_id, reason)`
- `mine_patterns(payload)`
- `list_patterns(scope=...)`
- `list_lessons(scope=...)`
- `synthesize(payload)`
- `get_synthesis(synthesis_run_id)`
- `list_skill_suggestions(scope=...)`
- `accept_skill_suggestion(suggestion_id, reason)`
- `reject_skill_suggestion(suggestion_id, reason)`
- `convert_skill_suggestion(suggestion_id, reason=..., approval_present=False)`
- `list_regression_suggestions(scope=...)`
- `accept_regression_suggestion(regression_suggestion_id, reason)`
- `reject_regression_suggestion(regression_suggestion_id, reason)`

The SDK exposes learning synthesis through public Brain APIs only. It does not
promote skills, create regression cases, call model providers, call external
observability tools, or import Brain internals.

## SelfModelResource

`client.self_model` supports:

- `describe(scope, include_capabilities=True, include_limitations=True, format="structured")`
- `capabilities(scope, status=None, capability_type=None)`
- `refresh_capabilities(scope, dry_run=True)`
- `create_limitation(payload)`
- `list_limitations(scope, status=None, category=None, severity=None, disclosure_required=None)`
- `seed_limitations(scope, dry_run=True)`
- `resolve_limitation(limitation_id, reason)`
- `calibrate_confidence(payload)`
- `list_confidence(trace_id=None, response_id=None, limit=100)`
- `run_assessment(payload)`
- `get_assessment(self_assessment_id)`
- `create_introspection(payload)`
- `get_introspection(introspection_snapshot_id, scope)`
- `list_introspection(scope, snapshot_type=None, status=None, limit=50)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, model
providers, frontend code, database clients, or external observability SDKs.

## ExplanationsResource

`client.explanations` supports:

- `explain(payload)`
- `get(explanation_id, scope)`
- `list(trace_id=None, target_type=None, target_id=None, limit=50)`
- `verify(explanation_id)`
- `why_not(payload)`
- `get_why_not(why_not_id, scope)`
- `trace_narrative(trace_id, payload)`
- `get_trace_narrative(trace_narrative_id, scope)`
- `list_trace_narratives(trace_id, limit=50)`
- `feedback(payload)`
- `list_feedback(**filters)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
database clients, provider SDKs, frontend code, or external observability
clients.

## InstructionsResource

`client.instructions` supports:

- `create_instruction(payload)`
- `get_instruction(instruction_id, scope)`
- `list_instructions(scope, status=None, instruction_type=None, scope_type=None, limit=100)`
- `disable_instruction(instruction_id, reason)`
- `resolve(payload)`
- `list_conflicts(scope, status=None, severity=None, limit=100)`
- `resolve_conflict(conflict_id, resolution, reason)`
- `create_preference(payload)`
- `list_preferences(scope, actor_id=None, workspace_id=None, status=None, preference_type=None, limit=100)`
- `confirm_preference(preference_id, reason)`
- `reject_preference(preference_id, reason)`
- `list_candidates(scope, status=None, preference_type=None, limit=100)`
- `confirm_candidate(candidate_id, reason)`
- `reject_candidate(candidate_id, reason)`
- `create_style_profile(payload)`
- `list_style_profiles(scope, actor_id=None, workspace_id=None, status=None, limit=100)`
- `effective_style(scope, actor_id=None, workspace_id=None)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
database clients, provider SDKs, frontend code, or external observability
clients.

## GroundingResource

`client.grounding` supports:

- `create_source(payload)`
- `get_source(grounding_source_id, scope)`
- `create_citation(payload)`
- `list_citations(response_id=None, explanation_id=None, source_id=None, limit=100)`
- `map_response(response_id, owner_scope, required_source_types=None)`
- `map_text(payload)`
- `verify(payload)`
- `get_verification(grounding_verification_id)`
- `coverage(payload)`
- `query(payload)`
- `unsupported(response_id=None, explanation_id=None, trace_id=None, limit=100)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, web
search clients, model providers, citation extraction services, database
clients, or frontend code.

## PromptsResource

`client.prompts` supports:

- `create_template(payload)`
- `list_templates(scope, status=None, template_type=None, limit=100)`
- `get_template(prompt_template_id, scope)`
- `seed_templates(scope, dry_run=True)`
- `create_fragment(payload)`
- `list_fragments(scope, status=None, fragment_type=None, limit=100)`
- `compile(payload)`
- `get_packet(prompt_packet_id, scope)`
- `list_packets(scope, trace_id=None, status=None, packet_type=None, limit=50)`
- `preview(payload)`
- `boundary_check(prompt_packet_id, scope)`
- `injection_findings(trace_id=None, prompt_packet_id=None, severity=None, status=None, limit=100)`
- `get_manifest(model_input_manifest_id, scope)`
- `list_manifests(scope, trace_id=None, prompt_packet_id=None, limit=50)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, model
providers, provider prompt SDKs, database clients, frontend code, or external
prompt optimization services.

## RunSupervisionResource

`client.run_supervision` supports:

- `create_run(payload)`
- `get_run(run_supervision_id, scope)`
- `list_runs(scope, target_system=None, status=None, stalled=None, limit=100)`
- `sample(run_supervision_id, scope)`
- `sample_many(scope, status="active", limit=100)`
- `archive(run_supervision_id, reason)`
- `create_control_request(payload)`
- `list_control_requests(run_supervision_id=None, status=None, control_type=None, limit=100)`
- `handoff_control(run_control_request_id, approval_present=False)`
- `create_timeout_policy(payload)`
- `list_timeout_policies(scope, status=None, target_system=None, run_type=None)`
- `create_compensation_plan(payload)`
- `propose_compensation(run_supervision_id, trigger_reason)`
- `get_compensation_plan(compensation_plan_id, scope)`
- `list_compensation_plans(scope, status=None, run_supervision_id=None, limit=100)`
- `approve_compensation_plan(compensation_plan_id, reason, approval_present=False)`
- `convert_compensation_to_action_proposals(compensation_plan_id, reason, approval_present=False)`
- `create_report(payload)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, target
subsystem internals, database clients, provider SDKs, frontend code, or
external orchestration clients.

## NotificationsResource

`client.notifications` supports:

- `create_topic(payload)`
- `list_topics(scope, status=None, category=None, limit=100)`
- `seed_default_topics(scope, dry_run=True)`
- `create_subscription(payload)`
- `list_subscriptions(scope, topic_key=None, actor_id=None, workspace_id=None, status=None, limit=100)`
- `publish(payload)`
- `query(payload)`
- `mark_read(notification_id, reason, actor_id=None)`
- `acknowledge(notification_id, reason, actor_id=None)`
- `resolve(notification_id, reason, actor_id=None)`
- `create_alert(payload)`
- `query_alerts(payload)`
- `acknowledge_alert(alert_id, reason, actor_id=None)`
- `resolve_alert(alert_id, reason, actor_id=None)`
- `create_escalation_policy(payload)`
- `list_escalation_policies(scope, status=None, topic_key=None, alert_type=None, limit=100)`
- `evaluate_escalations(scope, alert_id=None, notification_id=None)`
- `list_escalations(scope, status=None, severity=None, limit=100)`
- `create_digest(scope, digest_type="operator", actor_id=None, workspace_id=None, created_by=None)`
- `list_digests(scope, digest_type=None, limit=50)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
notification provider SDKs, email/SMS clients, webhook clients, database
clients, frontend code, or external delivery services.

## SchedulerResource

`client.scheduler` supports:

- `create_schedule(payload)`
- `get_schedule(schedule_id, scope)`
- `list_schedules(scope, status=None, schedule_type=None, target_type=None, limit=100)`
- `pause_schedule(schedule_id, scope, reason=None)`
- `resume_schedule(schedule_id, scope, reason=None)`
- `disable_schedule(schedule_id, scope, reason=None)`
- `delete_schedule(schedule_id, scope, reason=None)`
- `list_due_items(scope, schedule_id=None, status=None, missed=None, limit=100)`
- `create_reminder(payload)`
- `list_reminders(scope, status=None, reminder_type=None, actor_id=None, workspace_id=None, limit=100)`
- `acknowledge_reminder(reminder_id, scope, reason=None)`
- `snooze_reminder(reminder_id, scope, snoozed_until, reason=None)`
- `dismiss_reminder(reminder_id, scope, reason=None)`
- `tick(payload)`
- `run_tick(payload)`
- `get_tick_run(tick_run_id, scope)`
- `create_policy(payload)`
- `list_policies(scope, status=None, policy_type=None, limit=100)`
- `report(scope, trace_id=None)`
- `create_report(scope, trace_id=None)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
external calendar clients, notification provider SDKs, workflow engines,
database clients, frontend code, or external delivery services.

## IncidentsResource

`client.incidents` supports:

- `create_signal(payload)`
- `list_signals(scope, status=None, source_type=None, signal_type=None, severity=None, limit=100)`
- `dismiss_signal(incident_signal_id, reason, actor_id=None)`
- `create_incident(payload)`
- `get_incident(incident_id, scope)`
- `query(payload)`
- `acknowledge(incident_id, reason, actor_id=None)`
- `resolve(incident_id, reason, actor_id=None)`
- `dismiss(incident_id, reason, actor_id=None)`
- `archive(incident_id, reason, actor_id=None)`
- `create_rule(payload)`
- `list_rules(scope, status=None, rule_type=None, limit=100)`
- `seed_rules(scope, dry_run=True)`
- `correlate(payload)`
- `get_correlation_run(correlation_run_id)`
- `generate_root_causes(incident_id, scope, created_by=None)`
- `create_root_cause(payload)`
- `list_root_causes(incident_id=None, status=None, candidate_type=None, limit=100)`
- `confirm_root_cause(root_cause_candidate_id, reason, actor_id=None)`
- `dismiss_root_cause(root_cause_candidate_id, reason, actor_id=None)`
- `create_recovery_review(payload)`
- `get_recovery_review(recovery_review_id, scope)`
- `list_recovery_reviews(scope, incident_id=None, status=None, limit=100)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
external incident-management clients, notification provider SDKs, database
clients, frontend code, shell tools, or remediation systems.

## RegistryResource

`client.registry` supports:

- `upsert_resource(payload)`
- `get_resource(resource_type, resource_id, scope)`
- `get_by_uri(resource_uri, scope)`
- `query(payload)`
- `create_link(payload, scope)`
- `list_links(scope, source_uri=None, target_uri=None, relation_type=None, status=None, limit=100)`
- `list_backlinks(resource_uri, scope, limit=100)`
- `validate(payload)`
- `get_validation_run(validation_run_id, scope)`
- `list_broken_references(scope, status=None, severity=None, validation_run_id=None, limit=100)`
- `dismiss_broken_reference(broken_reference_id, reason, scope)`
- `list_orphaned_resources(scope, status=None, severity=None, validation_run_id=None, limit=100)`
- `dismiss_orphaned_resource(orphaned_resource_id, reason, scope)`
- `rebuild(payload)`
- `get_rebuild_run(rebuild_run_id, scope)`
- `create_snapshot(payload)`
- `get_snapshot(registry_snapshot_id, scope)`
- `list_snapshots(scope, snapshot_type=None, status=None, limit=50)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
database clients, search clients, graph clients, source-system internals,
frontend code, shell tools, or repair systems.

## LifecycleResource

`client.lifecycle` supports:

- `create_policy(payload)`
- `seed_default_policies(scope, dry_run=True)`
- `list_policies(scope, status=None, policy_type=None, retention_class=None, limit=100)`
- `get_policy(lifecycle_policy_id, scope)`
- `evaluate(payload)`
- `get_evaluation(lifecycle_evaluation_id, scope)`
- `list_classifications(scope, retention_class=None, lifecycle_state=None, limit=100)`
- `list_archive_candidates(scope, status=None, severity=None, limit=100)`
- `dismiss_archive_candidate(archive_candidate_id, reason, actor_id=None)`
- `convert_archive_candidate(archive_candidate_id, reason, actor_id=None, approval_present=False)`
- `list_redaction_candidates(scope, status=None, severity=None, limit=100)`
- `dismiss_redaction_candidate(redaction_candidate_id, reason, actor_id=None)`
- `convert_redaction_candidate(redaction_candidate_id, reason, actor_id=None, approval_present=False)`
- `create_purge_preview(resource_uris, scope, trace_id=None, created_by=None)`
- `list_purge_previews(scope, status=None, limit=100)`
- `review_candidate(payload)`
- `list_reviews(scope, candidate_type=None, decision=None, limit=100)`
- `report(scope, trace_id=None, created_by=None)`

The SDK calls public Brain APIs only. It does not import `aion_brain`,
database clients, object storage clients, source-system internals, frontend
code, shell tools, or external archive services.

## ContractsResource

`client.contracts` supports:

- `list_contracts(scope, contract_type=None, status=None, limit=100)`
- `list_interfaces(scope, interface_type=None, source_system=None, status=None, limit=100)`
- `create_snapshot(scope, snapshot_type="manual", trace_id=None)`
- `get_snapshot(contract_snapshot_id, scope)`
- `list_snapshots(scope, snapshot_type=None, status=None, limit=50)`
- `create_rule(payload)`
- `list_rules(scope, status=None, rule_type=None, limit=100)`
- `seed_rules(scope, dry_run=True)`
- `scan_compatibility(payload)`
- `get_scan(compatibility_scan_id)`
- `findings(status=None, severity=None, breaking=None, interface_type=None, limit=100)`
- `dismiss_finding(drift_finding_id, reason)`
- `migration_notes(scope, status=None, note_type=None, limit=100)`
- `report(scope, trace_id=None)`

The SDK calls public Contract Registry APIs only. It does not import
`aion_brain`, read source files, mutate source contracts, generate code,
execute migration steps, call external services, or expose raw secrets.

## ModuleBindingsResource

`client.module_bindings` supports:

- `create_slot(payload)`
- `get_slot(module_slot_id, scope)`
- `list_slots(scope, status=None, slot_type=None, extension_package_id=None, limit=100)`
- `archive_slot(module_slot_id, reason)`
- `delete_slot(module_slot_id, reason=None)`
- `create_binding(payload)`
- `get_binding(capability_binding_id, scope)`
- `list_bindings(scope, module_slot_id=None, status=None, capability_type=None, risk_level=None, limit=100)`
- `disable_binding(capability_binding_id, reason)`
- `validate(payload)`
- `get_validation(binding_validation_id)`
- `conflicts(scope, status=None, severity=None, limit=100)`
- `dismiss_conflict(binding_conflict_id, reason)`
- `create_mount_plan(module_slot_id, scope)`
- `get_mount_plan(mount_plan_id, scope)`
- `list_mount_plans(scope, status=None, module_slot_id=None, limit=100)`
- `create_route_preview(capability_binding_id, scope)`
- `list_route_previews(scope, module_slot_id=None, capability_binding_id=None, status=None, limit=100)`
- `query(payload)`

The SDK calls public Module Binding APIs only. It does not import
`aion_brain`, load extension code, install packages, activate capabilities,
register routes, mutate runtime configuration, execute mount plans, call
external services, or expose raw secrets.

## ModuleActivationResource

`client.module_activation` supports:

- `create_request(payload)`
- `list_requests(scope, status=None, module_slot_id=None, limit=100)`
- `get_request(activation_request_id, scope)`
- `archive_request(activation_request_id, payload)`
- `delete_request(activation_request_id, payload)`
- `run_gate(activation_request_id, payload)`
- `list_gate_runs(activation_request_id, scope, status=None, limit=100)`
- `list_blockers(scope, activation_request_id=None, status=None, severity=None, limit=100)`
- `dismiss_blocker(activation_blocker_id, payload)`
- `create_review(payload, scope=())`
- `list_reviews(scope, activation_request_id=None, decision=None, limit=100)`
- `create_plan(activation_request_id, payload)`
- `list_plans(scope, status=None, module_slot_id=None, limit=100)`
- `get_plan(activation_plan_id, scope)`
- `create_runtime_registration_preview(activation_request_id, payload)`
- `list_runtime_registration_previews(scope, activation_request_id=None, module_slot_id=None, status=None, limit=100)`
- `get_runtime_registration_preview(registration_preview_id, scope)`
- `query(payload)`

The SDK calls public Module Activation APIs only. It does not import
`aion_brain`, activate modules, register runtime routes, mutate runtime
configuration, invoke capabilities, call external services, or expose raw
secrets.

## Conformance Resource

`client.conformance` exposes the Capability Conformance Harness and readiness
assessment APIs. It calls public HTTP endpoints only and does not import Brain
API internals.

Useful methods include `create_profile`, `list_profiles`,
`seed_default_profiles`, `create_test_vector`, `generate_test_vectors`, `run`,
`list_findings`, `assess_readiness`, `list_readiness_assessments`, and `query`.

## GoldenPathResource

`client.golden_path` exposes the local Golden Path Scenario Harness.

Useful methods include:

- `create_scenario(payload)`
- `get_scenario(scenario_key, scope)`
- `list_scenarios(scope, status=None, scenario_type=None, limit=100)`
- `seed_default_scenarios(scope, dry_run=True)`
- `seed_default_fixtures(scope, dry_run=True)`
- `list_fixtures(scope, status=None, limit=100)`
- `run(payload)`
- `get_run(golden_path_run_id, scope=None)`
- `list_runs(scope, status=None, trace_id=None, limit=50)`
- `release_smoke(scope)`
- `get_report(golden_path_report_id, scope)`
- `list_reports(scope, status=None, limit=50)`
- `query(payload)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, execute
tools, call external services, call model providers, mutate non-scenario
records, run release packaging, or add frontend dependencies.

## ReleaseCandidateResource

`client.release_candidate` exposes the Release Candidate Gate APIs.

Useful methods include:

- `create_candidate(payload)`
- `list_candidates(scope, status=None, version=None, release_ready=None, limit=100)`
- `get_candidate(release_candidate_id, scope)`
- `create_matrix(payload)`
- `list_matrices(scope, status=None, limit=100)`
- `seed_default_matrices(scope, dry_run=True)`
- `run_gate(payload)`
- `get_run(rc_run_id, scope)`
- `list_findings(scope, status=None, severity=None, blocking=None, limit=100)`
- `dismiss_finding(rc_finding_id, scope, reason="dismissed")`
- `list_evidence_packs(scope, status=None, limit=50)`
- `get_evidence_pack(evidence_pack_id, scope)`
- `list_reports(scope, status=None, version=None, limit=50)`
- `get_report(rc_report_id, scope)`
- `query(payload)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, deploy,
publish, mutate source code, enable runtime features, call external services,
or add domain-specific release behavior.

## Local Demo SDK Flow

The local demo uses existing SDK resources only:

- `client.bootstrap`
- `client.golden_path`
- `client.release_candidate`
- `client.extensions`
- `client.module_bindings`
- `client.conformance`
- `client.operator`

The flow is setup doctor, golden path, RC gate, manifest validation, extension
intake dry-run, module binding validation dry-run, conformance readiness
assessment, and operator overview. It does not load code, activate bindings,
call external services, or mutate source code.

## ModuleMockRuntimeResource

`client.module_mock_runtime` exposes deterministic module mock runtime APIs.

Useful methods include:

- `create_profile(payload)`
- `seed_profiles(payload)`
- `list_profiles(scope, status=None, profile_type=None, limit=100)`
- `get_profile(mock_profile_id, scope)`
- `invoke(payload)`
- `list_runs(scope, status=None, capability_binding_id=None, limit=100)`
- `get_run(module_mock_run_id, scope)`
- `outputs(scope, module_mock_run_id=None, capability_binding_id=None, status=None, limit=100)`
- `get_output(module_mock_output_id, scope)`
- `list_findings(scope, status=None, severity=None, capability_binding_id=None, limit=100)`
- `dismiss_finding(module_mock_finding_id, payload)`
- `query(payload)`

The SDK calls public Brain APIs only. It does not import `aion_brain`, load
module code, install packages, activate modules, execute capabilities, register
routes, mutate runtime configuration, call external services, or add
domain-specific module behavior.

## ModelProviderHardeningResource

`client.model_provider_hardening` exposes provider hardening APIs.

Useful methods include:

- `create_profile(payload)`
- `seed_profiles(payload)`
- `list_profiles(scope, provider_key=None, status=None, risk_level=None, limit=100)`
- `get_profile(provider_profile_id, scope)`
- `egress_preview(payload)`
- `simulate(payload)`
- `assess_readiness(payload)`
- `blockers(scope, provider_key=None, status="open", severity=None, limit=100)`
- `dismiss_blocker(provider_blocker_id, payload)`
- `query(payload)`

The SDK does not expose provider-call or credential commands.

## Operator Console Strategy

AION-088 adds `client.operator_console` for read-only console view models and
contract audit access.

Methods:

- `list_views(scope)`
- `view_model(payload)`
- `audit(payload)`
- `workflows(scope)`
- `demo_map(scope)`

The SDK boundary remains unchanged: no frontend state, no runtime UI, no
privileged bypass, no module activation, no execution, no provider credentials,
no raw prompt exposure, no hidden reasoning exposure, no secret exposure, and
no external model calls.

## OperatorActionsResource

`client.operator_actions` exposes dry-run governed operator action APIs.

Useful methods include:

- `create_request(payload)`
- `get_request(operator_action_request_id, scope)`
- `list_requests(scope, status=None, action_type=None, target_type=None, limit=100)`
- `create_preview(operator_action_request_id, scope)`
- `previews(scope, status=None, limit=100)`
- `blockers(scope, operator_action_request_id=None, status=None, severity=None, limit=100)`
- `dismiss_blocker(operator_action_blocker_id, reason)`
- `review(operator_action_request_id, payload)`
- `reviews(scope, operator_action_request_id=None, decision=None, limit=100)`
- `query(payload)`

The SDK does not expose an execution command for operator actions.

## LocalAuthResource

`client.local_auth` exposes read-only/dev-only local auth APIs.

Useful methods include:

- `roles(scope)`
- `simulate(payload)`
- `filter_console(payload)`
- `audit(payload)`
- `status(scope)`

The SDK does not expose login, token, credential, session, production auth, or
external identity commands.

## LocalSessionResource

`client.local_session` exposes read-only/dev-only local session APIs.

Useful methods include:

- `preview(payload)`
- `context(payload)`
- `status(scope)`
- `boundary_check(scope)`
- `audit(payload)`

The SDK does not expose login, logout, token, cookie, credential, production
auth, persistent session, or external identity commands.

## Local Auth Role Matrix

`client.local_auth.role_matrix(scope)` returns the read-only role permission
proof matrix. `client.local_auth.role_access_audit(payload)` returns a role
access audit report. Neither method authorizes writes, execution, activation,
external calls, production auth, or session persistence.

## Action Authorization

`client.action_authorization.authorize(payload)` requests a dry-run
authorization decision. `client.action_authorization.audit(payload)` runs the
boundary audit, and `client.action_authorization.status(scope)` reads disabled
privileged-path flags. The SDK exposes no execute, activation, or external-call
method for action authorization.

## AuthRuntimeResource

`client.auth_runtime` exposes disabled auth-runtime status and mock-only preview
APIs.

Useful methods include:

- `status(scope)`
- `mock_claims_preview(payload)`
- `audit(payload)`

The SDK does not expose login, logout, token, cookie, session, credential,
provider, production auth, execution, activation, or external identity methods.

## ConnectorPolicyResource

`client.connector_policy` exposes connector policy catalog, matrix, dry-run,
traceability query, and status preview APIs.

Useful methods include:

- `catalog()`
- `matrix()`
- `dry_run(payload)`
- `query_traceability(payload)`
- `status(scope)`

The SDK does not expose connector runtime, external-call, credential, token,
provider, activation, route-registration, tool-execution, or write-execution
helpers for connector policy.
