# Epistemic Threat Model

AION-211 must handle these threats without enabling runtime effects.

- authority bias
- source-class treated as truth
- duplicated evidence amplification
- mirrored-source amplification
- circular citation
- provenance spoofing
- citation spoofing
- lineage spoofing
- independence-group spoofing
- stale evidence
- superseded evidence
- retracted evidence
- correction ignored
- jurisdiction mismatch
- version mismatch
- temporal mismatch
- missing scope
- selective evidence omission
- opposition suppression
- confidence inflation
- confidence underflow masking
- hard-cap bypass
- score-weight tampering
- hidden score weights
- manual FAIL-to-PASS conversion
- assessment used as approval
- user statement treated as fact
- engagement treated as fact
- unresolved contradiction hidden
- source body leakage
- claim text leakage into diagnostics
- raw prompt leakage
- persistent assessment write
- database creation
- network acquisition
- background mutation
- knowledge-promotion bypass
- cognitive-belief mutation
- authorization reuse

Core rule: the epistemic engine calculates a bounded evidence assessment. It does not provide metaphysical certainty.

## AION-211 Implementation Update

AION-211 now implements the deterministic epistemic evidence-assessment engine under `AION-210-KI-0004`. The engine is in-memory, deterministic, transparent, versioned, and read-only. It evaluates evidence posture, source independence, support, opposition, freshness, scope applicability, corrections, retractions, supersession, unresolved contradiction, bounded confidence, confidence bands, hard caps, integrity, diagnostics, fixture replay, exact queries, and operator-review evidence.

It remains runtime-disabled and persistent-write-disabled. It is not an absolute truth oracle, automatically accepts or rejects no claim, promotes no knowledge, mutates no cognitive belief, calls no network, creates no database, and creates no v0.2 tag or release. AION-212 is the next formal closeout task.
