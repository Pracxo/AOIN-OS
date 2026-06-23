# Module Activation Threat Model

## Purpose

This threat model records the risks that must be controlled before any future
module activation path can exist. AION-082 and AION-083 add no activation, code
loading, package installation, dynamic route registration, or external calls.
AION-083 adds metadata-only activation requests, blockers, reviews, plans, and
runtime registration previews.

| Threat category | Likely entry point | Current v0.1 control | Future required control | No-go condition |
| --- | --- | --- | --- | --- |
| Malicious manifest metadata | Extension manifest | Metadata validation, operator review, policy gate | Signed manifest provenance and stricter schema compatibility | Manifest requests unsafe permissions or misrepresents capabilities |
| Dependency confusion | Declared dependencies | Dependency download disabled | Package lock, allowlist, provenance, isolated resolver | Any undeclared or remote dependency install |
| Hidden executable payload | Package metadata | Payload execution disabled | Artifact scanner and sandbox staging | Any payload that can execute before approval |
| Route hijack attempt | Declared route preview | Dynamic route registration disabled | Route namespace reservation and conflict checks | Route overlaps Brain core or active public APIs |
| Policy action escalation | Declared policy actions | Generic policy vocabulary and policy coverage | Permission diff review and least-privilege grants | Module asks for actions outside approved scope |
| Prompt injection through module docs | Module docs or descriptions | Docs are metadata and not executable | Content scanning and prompt-governed compilation | Instructions attempt to override Brain policy or operator control |
| Secret access request | Declared settings or permissions | Raw secret access disabled | Secret broker with scoped grants and audit | Module asks for raw secret material |
| External source download | Source metadata | External sources disabled | Provenance verification and offline mirror policy | Runtime depends on live download to activate |
| Sandbox escape request | Sandbox profile | Sandbox execution disabled | Sandbox policy, resource limits, syscall and network controls | Module requires host access outside sandbox |
| Capability overreach | Capability binding | Binding validation and conformance | Runtime permission grants and risk review | Capability scope exceeds manifest purpose |
| Tool execution bypass | Runtime or capability invocation | Tool intent blocker and action proposal broker | Tool execution broker with approval and replayable audit | Module can call tools outside broker |
| Model output tool intent bypass | Model output governance | Tool intent capture and blocker | Output-to-action review with explicit approval | Generated output triggers action without review |
| Data exfiltration | Memory, evidence, logs, or runtime | Local-only records and redaction | Egress policy and data access audit | Module requests uncontrolled egress |
| Unsafe autonomy escalation | Autonomy settings | Full autonomy disabled | Autonomy policy with staged approvals | Module asks to self-approve or self-execute |
| Lifecycle purge abuse | Lifecycle actions | Hard delete disabled | Retention governance and review-backed purge | Module requests irreversible record removal |
| Audit/provenance tampering | Audit and provenance records | Append-only posture and integrity checks | Tamper-evident module events | Module can alter or remove review history |
