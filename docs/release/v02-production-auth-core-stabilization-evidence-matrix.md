# v0.2 Production Auth Core Stabilization Evidence Matrix

| Evidence | Artifact | Expected state | No-go condition |
| --- | --- | --- | --- |
| Authorization lineage | `ProductionAuthCoreConfig` | AION-151 historical and AION-153 stabilization fields are separate | AION-153 overwrites AION-151 lineage |
| Canonical serialization | `aion_brain.production_auth.canonical` | deterministic UTF-8 JSON and SHA-256 fingerprints | mutation, random ordering, NaN, infinity, or memory-address values |
| Reason-code registry | `aion_brain.production_auth.reason_codes` | immutable, ordered, unique registry | unknown or duplicate reason code accepted |
| Operation taxonomy | `ProductionAuthPolicyRequest` | internal preview operations only | login/logout/callback/token/session/provider operations accepted |
| Evidence immutability | frozen evidence models | assignment and metadata mutation fail | mutable audit, provenance, decision, or diagnostic evidence |
| Config matrix | `PROHIBITED_RUNTIME_FIELDS` | every true runtime setting fails closed | any prohibited setting accepted as true |
| Redaction | production-auth contracts | protected material rejected in nested metadata and source refs | credentials, tokens, cookies, provider payloads, prompts, or hidden reasoning stored |
| Kernel and routes | kernel diagnostics and route table | service assembled, runtime disabled, no production-auth route | public production-auth API surface appears |
| Performance smoke | focused pytest | canonicalization, fingerprinting, and blocked decisions stay within CI-safe limits | dependency or machine-sensitive benchmark added |
