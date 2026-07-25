# Epistemic Assessment Contracts

AION-211 adds strict Pydantic v2 contracts for assessment requests, explicit freshness policy, explicit target scope, evidence contributions, role evidence scores, scorecard policy, hard-cap applications, claim-level assessments, immutable assessment batches, exact queries, resource budgets, synthetic fixture replay, integrity reports, incidents, diagnostics, evidence bundles, and operator-review items.

Every contract is extra-field-forbid, UTC-bound where timestamps are present, fingerprinted with canonical JSON, and redacted. The contracts carry AION-210-KI-0004 lineage where the object represents a batch, fixture, evidence bundle, authorization, or runtime-hold evidence.

Forbidden output remains absent or false: absolute truth, automatic claim acceptance, automatic claim rejection, contradiction resolution, knowledge promotion, belief creation, belief mutation, persistent writes, and runtime effects.
