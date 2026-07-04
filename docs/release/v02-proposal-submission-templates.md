# v0.2 Proposal Submission Templates

## Purpose

These templates define the required shape for future implementation requests. They are planning-only templates and do not approve implementation.

## Template Fields

Each template must include workstream, problem statement, proposed change, runtime capability requested, current approval state, required ADR, required gate, required evidence, security impact, policy impact, rollback/audit plan, and default approval status false.

## Production Auth Implementation Request

- workstream: production auth implementation
- problem statement: define the auth runtime problem to solve
- proposed change: describe the proposed auth boundary change
- runtime capability requested: production auth runtime
- current approval state: false
- required ADR: production auth implementation ADR
- required gate: production auth implementation gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: identity, session, credential, token, and provider boundaries
- policy impact: auth policy, denial policy, audit policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Audit/Provenance Hardening Request

- workstream: audit/provenance hardening
- problem statement: define the audit evidence gap
- proposed change: describe the proposed audit or provenance hardening change
- runtime capability requested: audit hardening runtime
- current approval state: false
- required ADR: audit/provenance hardening ADR
- required gate: audit/provenance hardening gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: integrity, redaction, retention, and review boundaries
- policy impact: audit policy and provenance policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Rollback/Recovery Request

- workstream: rollback/recovery
- problem statement: define the recovery gap
- proposed change: describe the proposed rollback or recovery change
- runtime capability requested: rollback/recovery runtime
- current approval state: false
- required ADR: rollback/recovery ADR
- required gate: rollback/recovery gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: recovery authorization, effect verification, and audit boundaries
- policy impact: rollback policy and recovery policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## External Call Release Gate Request

- workstream: external call release gate
- problem statement: define the external-call governance gap
- proposed change: describe the proposed external-call gate
- runtime capability requested: external call runtime
- current approval state: false
- required ADR: external call release gate ADR
- required gate: external call release gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: egress, provider, credential, token, and data exposure boundaries
- policy impact: egress policy and provider policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Connector Runtime Implementation Request

- workstream: connector runtime implementation
- problem statement: define the connector runtime gap
- proposed change: describe the proposed connector runtime boundary
- runtime capability requested: connector runtime
- current approval state: false
- required ADR: connector runtime implementation ADR
- required gate: connector runtime implementation gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: connector egress, ingress, credentials, tokens, sandbox, and activation boundaries
- policy impact: connector policy and runtime denial policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Credential Store Implementation Request

- workstream: credential store implementation
- problem statement: define the credential boundary gap
- proposed change: describe the proposed credential store boundary
- runtime capability requested: credential store runtime
- current approval state: false
- required ADR: credential store implementation ADR
- required gate: credential store implementation gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: protected-material persistence, redaction, rotation, revocation, and access boundaries
- policy impact: credential policy and audit policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Sandbox Runtime Implementation Request

- workstream: sandbox runtime implementation
- problem statement: define the sandbox boundary gap
- proposed change: describe the proposed sandbox runtime boundary
- runtime capability requested: sandbox runtime
- current approval state: false
- required ADR: sandbox runtime implementation ADR
- required gate: sandbox runtime implementation gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: filesystem, process, network, package, import, and execution boundaries
- policy impact: sandbox policy and denial policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Operator Write Execution Request

- workstream: operator write execution
- problem statement: define the write execution gap
- proposed change: describe the proposed write execution boundary
- runtime capability requested: operator write execution
- current approval state: false
- required ADR: operator write execution ADR
- required gate: operator write execution gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: approval, separation of duties, effect verification, and rollback boundaries
- policy impact: write policy and approval policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Module Activation Request

- workstream: module activation
- problem statement: define the activation gap
- proposed change: describe the proposed module activation boundary
- runtime capability requested: module activation runtime
- current approval state: false
- required ADR: module activation implementation ADR
- required gate: module activation implementation gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: code loading, runtime registration, capability activation, package installation, and audit boundaries
- policy impact: module policy and activation denial policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## Production UI Decision Request

- workstream: production UI decision
- problem statement: define the production UI decision gap
- proposed change: describe the proposed UI decision boundary
- runtime capability requested: production UI runtime
- current approval state: false
- required ADR: production UI decision ADR
- required gate: production UI decision gate
- required evidence: security review, architecture review, operator review, rollback/audit plan, no-go regression
- security impact: operator visibility, approvals, auditability, auth, and write controls
- policy impact: UI policy and operator policy
- rollback/audit plan: rollback steps and retained audit evidence required
- default approval status false

## AION-132 Submission Freeze

AION-132 freezes these templates as planning-only submissions. Template
completion can satisfy evidence completeness but cannot approve implementation,
queue items, proposal implementation, runtime capability, v0.2 tag creation,
or v0.2 release creation.

## AION-133 Final Review

AION-133 requires future template submissions to pass request pack final review,
pre-approval submission freeze, and final no-go regression before approval
consideration. Template completion remains planning-only and cannot approve
submission, implementation, queue items, runtime capability, v0.2 tag creation,
or v0.2 release creation.
