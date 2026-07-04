# v0.2 Request Package Review Rules

## Request Completeness Review

Reviewers must confirm that every request includes the required proposal fields, evidence fields, ADR dependency, gate dependency, review requirements, rollback/audit plan, and no-go acknowledgement.

## Duplicate Handling

Duplicate requests must be linked, consolidated, or rejected. Duplicate handling cannot approve implementation or bypass required evidence.

## Evidence Sufficiency Review

Reviewers must confirm evidence quality before approval consideration. Evidence sufficiency does not approve implementation by itself.

## Security Review

Security review must evaluate external calls, credential handling, token handling, auth runtime, sandbox execution, operator write execution, module activation, code loading, and privileged bypass controls.

## Architecture Review

Architecture review must evaluate service boundaries, API surfaces, SDK and CLI surfaces, runtime configuration, data lifecycle, audit records, failure modes, rollback behavior, and no-domain-drift impact.

## Operator Review

Operator review must evaluate read/write separation, preview versus execution behavior, approval visibility, denial states, incident recovery, auditability, and rollback procedures.

## ADR Dependency Review

ADR dependency review must confirm that the required ADR exists or is explicitly required before any future approval consideration. ADR review cannot enable runtime by itself.

## Gate Dependency Review

Gate dependency review must confirm that the required gate exists or is explicitly required before any future approval consideration. Gate success cannot enable runtime by itself.

## Rejection Rules

Requests are rejected if required evidence is missing, approval records are missing, ADR dependencies are bypassed, gate dependencies are bypassed, approval queue item approval is true, proposal implementation approval is true, runtime implementation approval is true, or any no-go condition is present.

## No Direct Implementation Approval

The request package does not directly approve implementation. Future implementation still requires explicit approval records, ADRs, gate evidence, security review, architecture review, operator review, rollback/audit evidence, and no-go regression evidence.
