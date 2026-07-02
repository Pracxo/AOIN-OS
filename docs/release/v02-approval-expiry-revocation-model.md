# v0.2 Approval Expiry And Revocation Model

## Approval Expiry Rule

Every future approval record must include an expiry date or event. Expired
approval returns to not approved and cannot be reused for implementation.

## Approval Revocation Rule

Approval may be revoked by failed gate evidence, failed no-go regression,
security rejection, architecture rejection, operator rejection, scope drift,
release blocker discovery, or stale evidence.

## Evidence Refresh Requirement

Approval evidence must be refreshed after expiry, revocation, branch drift,
scope drift, dependency drift, policy drift, security posture changes, or failed
checks.

## Re-Review Triggers

Re-review is required after changed runtime capability, changed rollback plan,
changed ADR, changed gate dependency, changed reviewer set, changed security
impact, changed policy impact, changed audit/provenance impact, or changed
release risk.

## Expired Approval Behaviour

Expired approval behaves as not approved. Implementation cannot start and no
runtime capability is enabled.

## Revoked Approval Behaviour

Revoked approval behaves as not approved. Implementation cannot continue until
the revocation reason is resolved and fresh approval evidence is recorded.

## Audit/Provenance Requirement

Expiry, revocation, re-review, decision status, reviewer identity, evidence
references, and no-go findings must be auditable through repository-local
records.

## Approval Does Not Execute

Approval does not execute tools, action proposals, write paths, hard deletes,
runtime route registration, module activation, connector calls, or sandbox
execution.

## Approval Does Not Enable Runtime By Itself

Approval does not enable runtime by itself. Runtime still requires a future
scoped implementation task, explicit approval record, scoped ADR, scoped gate,
no-go regression, local checks, and release review.

## AION-124 Intake Requirement

AION-124 requires workstream intake records to include approval expiry status
and revocation path evidence before planning review. Missing expiry or
revocation evidence rejects the workstream and keeps implementation approval
false.
