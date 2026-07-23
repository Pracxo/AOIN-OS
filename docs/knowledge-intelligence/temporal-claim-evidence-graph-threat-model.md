# Temporal Claim-Evidence Graph Threat Model

The temporal claim-evidence graph represents assertions, evidence, time, jurisdiction, version, and relationships. It does not decide truth.

## Threats

- claim identity collision
- claim text injection
- raw prompt stored as claim
- hidden reasoning stored as claim
- user statement treated as fact
- engagement signal treated as fact
- malformed subject-predicate-object structure
- claim normalization collision
- source-registry reference spoofing
- citation spoofing
- provenance spoofing
- lineage-group spoofing
- evidence misbinding
- unsupported claim with no evidence
- duplicate evidence amplification
- mirror sources treated as independent
- source classification treated as truth
- jurisdiction mismatch
- version mismatch
- timezone ambiguity
- open-ended temporal interval ambiguity
- overlapping interval error
- non-overlapping historical claims treated as contradictory
- current claim superseding historical claim incorrectly
- correction relation tampering
- retraction relation tampering
- supersession cycles
- self-support relation
- self-contradiction relation
- relation-edge explosion
- graph query flooding
- graph fixture tampering
- persistent graph write
- graph-database creation
- claim verification bypass
- truth assignment bypass
- confidence assignment bypass
- knowledge-promotion bypass
- cognitive-belief mutation
- source-body leakage
- network acquisition
- background graph mutation
- authorization reuse
- evaluation evidence used as approval

## Hard Boundary

Claim verification, truth assignment, confidence assignment, knowledge promotion, cognitive-belief mutation, source-body leakage, persistent graph write, graph-database creation, network acquisition, background graph mutation, authorization reuse, and evaluation evidence used as approval remain prohibited.
