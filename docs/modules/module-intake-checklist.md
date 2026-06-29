# Module Intake Checklist

Use this checklist before a module can move from manifest review to later
activation design.

- [ ] manifest is valid
- [ ] no executable payload
- [ ] no external dependency download
- [ ] no full autonomy request
- [ ] no raw secret access request
- [ ] no dynamic route registration
- [ ] no policy escalation
- [ ] declared contracts exist
- [ ] declared settings exist
- [ ] sandbox requirement declared
- [ ] capability binding validates
- [ ] conformance passes
- [ ] readiness assessment created
- [ ] activation_ready=false
- [ ] module mock profile is metadata-only if present
- [ ] module mock invocation uses `mode=dry_run` if present
- [ ] module mock output is synthetic if present
- [ ] module mock evidence keeps external_calls_made=false
- [ ] module mock evidence keeps code_loaded=false
- [ ] operator review recorded
- [ ] audit/provenance present
- [ ] release/freeze gates remain green

Activation remains disabled until a future activation gate exists.

Code loading remains disabled for all metadata examples and intake records.

Modules must not modify Brain core.

## First Module Pack Checklist

For `generic.knowledge_intelligence`, verify:

- [ ] `examples/modules/generic-knowledge-intelligence/manifest.json` exists
- [ ] `./scripts/module-pack-check.sh` passes
- [ ] `./scripts/generic-knowledge-demo.sh --offline-ok --skip-api` passes
- [ ] all five capabilities begin with `generic.`
- [ ] declared routes are empty
- [ ] declared dependencies are empty
- [ ] capability bindings use `target_runtime=metadata_only`
- [ ] capability bindings keep `controlled_supported=false`
- [ ] test vectors are synthetic
- [ ] readiness expects `activation_ready=false`
- [ ] activation request expects `activation_allowed=false`
- [ ] mock-profile.json contains no executable simulation rules
- [ ] mock-invocation-request.json uses `mode=dry_run`
- [ ] mock-output-example.json sets `synthetic=true`
- [ ] runtime registration preview expectations keep `registration_allowed=false`
- [ ] operator review states approval does not activate

## AION-105 Pre-Gate Checklist

Before any future activation implementation, verify:

- [ ] `./scripts/module-activation-design-review.sh` passes
- [ ] `./scripts/module-activation-no-go-regression.sh` passes
- [ ] plugin boundary evidence pack is current
- [ ] code loading disabled proof is current
- [ ] runtime registration disabled proof is current
- [ ] capability activation disabled proof is current
- [ ] lifecycle traceability matrix is current
- [ ] threat model, sandbox design, package trust model, rollback design,
      operator approval model, audit/provenance design, and release gate are
      approved by ADR
- [ ] activation, execution, registration, and module writes remain disabled
