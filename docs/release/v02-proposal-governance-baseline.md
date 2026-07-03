# v0.2 Proposal Governance Baseline

## Baseline

The proposal registry remains preview-only. The approval queue remains preview-only. Proposal implementation approval remains false. Approval queue item approval remains false.

## Required ADR Dependency

Every future implementation proposal must cite a required ADR dependency before implementation can be considered. A missing ADR dependency blocks the proposal.

## Required Gate Dependency

Every future implementation proposal must cite a required gate dependency before implementation can be considered. A missing gate dependency blocks the proposal.

## Required Security Review

Every future implementation proposal must include security review evidence covering threat model impact, credential/token impact, external-call impact, sandbox impact, and no-go regression impact.

## Required Architecture Review

Every future implementation proposal must include architecture review evidence covering runtime boundaries, API boundaries, SDK/CLI boundaries, data ownership, rollback posture, and release blockers.

## Required Operator Review

Every future implementation proposal must include operator review evidence covering console visibility, dry-run behavior, write-path restrictions, safety blockers, and operational rollback.

## Required Rollback And Audit Evidence

Every future implementation proposal must include rollback/audit evidence before approval can be considered. Rollback and audit evidence are descriptive until a later scoped implementation approval task widens scope.

## No Direct Implementation Approval

No proposal registry entry, approval queue preview, reviewer note, static console panel, or planning checklist can directly approve implementation. Future implementation requires explicit scoped approval records, ADRs, gate evidence, security review, architecture review, operator review, and rollback/audit evidence.

## AION-129 Final Planning Release Gate

AION-129 promotes this governance baseline into the final planning release
gate. Proposal registry entries remain preview-only, approval queue entries
remain preview-only, proposal implementation approval remains false, approval
queue item approval remains false, and future implementation still requires a
separate scoped approval task.
