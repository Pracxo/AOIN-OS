# v0.2 Implementation Request Pack

## Purpose

AION-131 creates the standard request package that future v0.2 workstreams must complete before implementation can be considered. The pack sits on top of the AION-130 governance handoff baseline and does not approve implementation.

## Scope

This request pack is planning and evidence-boundary work only. It covers request documents, proposal templates, evidence checklists, synthetic examples, static console preview data, local scripts, and regression tests. It does not create a v0.2 tag, create a release, mutate the v0.1 baseline, add runtime code, add API routes, add SDK resources, add CLI command implementations, add package files, add migrations, call external services, store credentials, store tokens, enable production auth, enable connector runtime, enable operator write execution, enable sandbox execution, enable module activation, enable capability activation, enable code loading, or enable runtime registration.

## Request Pack Contents

- Implementation request summary
- Proposal submission template
- Approval evidence boundary
- Implementation request evidence checklist
- Workstream request template catalog
- Request package review rules
- Request package no-go checks
- Synthetic examples
- Static console request pack preview data

## Required Proposal Fields

Every proposal must include workstream, problem statement, proposed change, runtime capability requested, current approval state, required ADR, required gate, required evidence, security impact, architecture impact, policy impact, rollback/audit plan, no-go acknowledgement, and default approval status false.

## Required Evidence Fields

Every request pack must include risk statement, security impact, architecture impact, policy impact, audit/provenance impact, rollback plan, ADR dependency, gate dependency, test evidence, no-go acknowledgement, and approval status false.

## Required ADR Dependency

Each request must identify the ADR that will govern future implementation. ADR review is required before approval consideration, but ADR review does not enable runtime by itself.

## Required Gate Dependency

Each request must identify the local gate that will verify future implementation scope. Gate success is required before approval consideration, but gate success does not enable runtime by itself.

## Required Security Review

Every request must describe security impact for external calls, credential handling, token handling, auth runtime, sandbox execution, operator write execution, module activation, code loading, and privileged bypass controls.

## Required Architecture Review

Every request must describe architecture impact for service boundaries, API surfaces, SDK and CLI surfaces, runtime configuration, data lifecycle, audit records, failure modes, rollback behavior, and no-domain-drift impact.

## Required Operator Review

Every request must describe operator impact for preview versus execution behavior, approval visibility, denial states, incident recovery, auditability, and rollback procedures.

## Required Rollback/Audit Plan

Every request must include rollback steps, audit records, effect verification, approval traceability, failure recovery, revocation behavior, and retained evidence.

## Default Implementation Approval False

Every request pack and proposal template defaults to `runtime_implementation_approved=false`, `workstream_implementation_approved=false`, `proposal_implementation_approved=false`, and `approval_queue_item_approved=false`.

## No v0.2 Tag Or Release

AION-131 explicitly creates no v0.2 tag and no v0.2 release. The `aion-v0.1.0` tag remains the frozen release baseline.

## AION-132 Stabilization

AION-132 stabilizes this request pack with an evidence completeness gate and
submission freeze. The request pack remains preview-only and keeps
`request_pack_approval=false`, `evidence_completeness_bypassed=false`,
`submission_freeze_bypassed=false`, `approval_queue_item_approved=false`,
`proposal_implementation_approved=false`, and
`runtime_implementation_approved=false`.

## AION-133 Final Review

AION-133 performs the final pre-approval request-pack review on top of this
pack and the AION-132 stabilization gate. The request pack remains
preview-only, submission approval remains false, preapproval gate bypass remains
false, and no v0.2 tag, v0.2 release, runtime implementation, API route, SDK
resource, CLI command, package file, or migration is added.

## AION-134 Submission Registry Preview

AION-134 catalogs future implementation request candidates from this pack in a
submission registry preview. Candidate records are planning-only and keep
request pack approval, submission approval, preapproval queue item approval,
implementation approval, runtime enablement, v0.2 tag creation, and v0.2
release creation false.

## AION-135 Submission Registry Stabilization Dependency

AION-135 uses the implementation request pack as candidate context only. The
pack does not approve implementation, does not approve request items, does not
approve submissions, does not enable runtime, does not add API or SDK
execution surfaces, and does not create a v0.2 tag or release.
