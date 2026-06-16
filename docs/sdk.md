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
