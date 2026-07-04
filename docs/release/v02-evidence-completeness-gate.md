# v0.2 Evidence Completeness Gate

## Required Problem Statement

Every future implementation request must describe the problem it intends to
solve before review can begin.

## Required Risk Statement

Every future implementation request must describe security, operational, data,
and rollback risk before review can begin.

## Required Security Impact

Every future implementation request must describe the security impact of auth,
external calls, protected-material handling, sandbox execution, operator write
execution, module activation, code loading, and privileged bypass controls.

## Required Architecture Impact

Every future implementation request must describe service boundaries, API
surfaces, SDK and CLI surfaces, runtime configuration, data lifecycle, audit
records, failure modes, rollback behavior, and no-domain-drift impact.

## Required Policy Impact

Every future implementation request must describe policy impact, denial states,
approval dependencies, and no-go enforcement before review can begin.

## Required Audit/Provenance Impact

Every future implementation request must describe audit records, provenance
records, redaction, retained evidence, and effect verification.

## Required Rollback Plan

Every future implementation request must include rollback steps, failure
recovery, revocation behavior, and verification evidence.

## Required ADR Dependency

Every future implementation request must identify the ADR dependency required
before implementation can be considered.

## Required Gate Dependency

Every future implementation request must identify the local gate dependency
required before implementation can be considered.

## Required Test Evidence

Every future implementation request must identify the test evidence required to
prove scope, safety, denial behavior, and rollback behavior.

## Required No-Go Acknowledgement

Every future implementation request must acknowledge no-go conditions and treat
any violation as a release blocker and approval blocker.

## Required Approval Status False

Every future implementation request must keep request pack approval, proposal
implementation approval, approval queue item approval, workstream
implementation approval, backlog implementation approval, and runtime
implementation approval false until a later scoped approval task explicitly
changes that state.

## AION-133 Final Review Dependency

AION-133 treats this evidence completeness gate as required inherited evidence
for final request-pack review. Evidence completeness remains non-approval
evidence, and request pack approval, submission approval, preapproval gate
bypass, runtime implementation approval, v0.2 tag creation, and v0.2 release
creation remain false.
